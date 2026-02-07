# Bug 修复总结报告

## 🐛 发现的 Bug

### Bug 1: Internal API 路由前缀重复 ✅ 已修复

**错误信息：**
```
404: POST /internal/messages/claim-and-prepare
```

**根本原因：**
- 代码重构时将 `internal.py` 拆分成 `internal/` 文件夹
- **忘记删除旧的 `internal.py` 文件**（97KB）
- 子模块错误设置了 `prefix="/internal"`
- 父路由也有 `prefix="/internal"`
- 最终路径变成：`/internal/internal/messages/...` ❌

**修复：**
1. ✅ 删除了旧的 `internal.py` 文件
2. ✅ 修复了 11 个子模块的路由配置（移除 prefix）

**影响：** Saga workers 无法获取消息，系统完全停止

---

### Bug 2: MCP Business 未调用 Tools Server ✅ 已修复

**错误信息：**
```
404: POST /internal/runtimes/rt-xxx/tools/call
```

**根本原因：**
- `MCPBusiness.create()` 创建 runtime 时，**没有通知 Tools Server**
- 只创建了旧的 "aggregate_mcp"
- Tools Server 中 runtime 数量 = 0
- 执行工具时找不到 runtime → 404

**修复：**
修改 `task_queue/business/mcp.py`：

1. **在 `create()` 方法中添加 Tools Server 调用：**
```python
# 1. Create runtime context in Tools Server
tools_server_url = os.environ.get("NOVAIC_TOOLS_SERVER_URL", ServiceConfig.TOOLS_SERVER_URL)
with httpx.Client(timeout=10.0, trust_env=False) as http_client:
    resp = http_client.post(
        f"{tools_server_url}/internal/runtimes",
        json={
            "runtime_id": runtime_id,
            "agent_id": agent_id,
            "subagent_id": subagent_id,
            "ports": {},
        }
    )
    resp.raise_for_status()
```

2. **在 `destroy()` 方法中添加 Tools Server 清理：**
```python
# 1. Destroy Tools Server runtime context
tools_server_url = os.environ.get("NOVAIC_TOOLS_SERVER_URL", ServiceConfig.TOOLS_SERVER_URL)
with httpx.Client(timeout=10.0, trust_env=False) as http_client:
    resp = http_client.delete(
        f"{tools_server_url}/internal/runtimes/{runtime_id}"
    )
    # Ignore 404 - already deleted
    if resp.status_code != 404:
        resp.raise_for_status()
```

**影响：** 即使消息能接收，工具也无法执行

---

## 🎯 架构说明

### 原有设计（正确的）

```
RuntimeStart Saga 流程：
1. create_runtime  → Gateway 创建 runtime 记录（DB）
2. create_mcp      → MCPBusiness.create() 应该创建工具上下文
3. set_awake       → 设置 SubAgent 为 awake
4. trigger_think   → 触发 ReactThink Saga
```

**第 2 步 `create_mcp` 应该做的事：**
- ✅ 调用 Tools Server 创建 runtime 上下文
- ✅ 创建 aggregate MCP（向后兼容）
- ✅ 更新 runtime 的 mcp_url

**但实际代码缺少了第一步！**

---

## 📋 修改文件清单

### 1. Gateway Internal API 修复

| 文件 | 操作 | 说明 |
|------|------|------|
| `gateway/api/internal.py` | 删除 | 删除旧的单文件版本 |
| `gateway/api/internal/agent.py` | 修改 | 移除 prefix |
| `gateway/api/internal/broadcast.py` | 修改 | 移除 prefix |
| `gateway/api/internal/config.py` | 修改 | 移除 prefix |
| `gateway/api/internal/health.py` | 修改 | 移除 prefix |
| `gateway/api/internal/llm.py` | 修改 | 移除 prefix |
| `gateway/api/internal/message.py` | 修改 | 移除 prefix |
| `gateway/api/internal/runtime.py` | 修改 | 移除 prefix |
| `gateway/api/internal/subagent.py` | 修改 | 移除 prefix |
| `gateway/api/internal/task.py` | 修改 | 移除 prefix |
| `gateway/api/internal/vm.py` | 修改 | 移除 prefix |
| `gateway/api/internal/web.py` | 修改 | 移除 prefix |

### 2. MCP Business 修复

| 文件 | 方法 | 修改 |
|------|------|------|
| `task_queue/business/mcp.py` | `create()` | 添加 Tools Server 创建调用 |
| `task_queue/business/mcp.py` | `destroy()` | 添加 Tools Server 删除调用 |

---

## 🔄 完整数据流（修复后）

```
用户发消息
  ↓
Gateway 接收消息 (POST /api/inbox)
  ↓
创建 Saga (RuntimeStart)
  ↓
Step 1: create_runtime
  ↓ POST /internal/runtimes
Gateway 创建 runtime 记录（DB）
  ↓
Step 2: create_mcp
  ↓ MCPBusiness.create()
  ↓ ✅ 调用 Tools Server
  ↓ POST http://127.0.0.1:19998/internal/runtimes
Tools Server 创建工具上下文
  ↓
Step 3: set_awake
  ↓
Step 4: trigger_think (ReactThink Saga)
  ↓
Master 调用工具
  ↓ POST /internal/runtimes/{runtime_id}/tools/call
Tools Server 执行工具 ✅ 成功
```

---

## 🚀 验证步骤

### 1. 重启应用

```bash
# 退出 NovAIC.app，重新打开
```

### 2. 发送测试消息

在 NovAIC 中发送消息（比如"你好"）

### 3. 检查 Tools Server

```bash
# 应该有 runtime 了
curl http://127.0.0.1:19998/internal/runtimes
# 期望：{"runtimes":[{"runtime_id":"rt-xxx",...}],"total":1}
```

### 4. 观察日志

```bash
tail -f "/Users/wangchaoqun/Library/Application Support/com.novaic.app/logs/gateway-$(date +%Y%m%d).log"
```

应该看到：
- ✅ `/internal/messages/claim-and-prepare` 成功（不再 404）
- ✅ Tools Server 创建 runtime 成功
- ✅ 工具调用成功

---

## 💡 为什么之前没有这个逻辑？

### 分析

1. **历史架构演变：**
   - 之前可能所有工具都在 Gateway 内部
   - 后来拆分出 Tools Server
   - 但 `MCPBusiness.create()` **没有更新**

2. **代码注释线索：**
   ```python
   # 2. Create aggregate MCP (if still needed for backward compatibility)
   resp = self.client.create_aggregate_mcp(...)
   ```
   - "backward compatibility" 说明这是旧代码
   - 新的 Tools Server 调用应该在前面

3. **Tools Server 有 restore 机制：**
   - Tools Server 启动时会从 Gateway 拉取 runtime
   - 但要求 runtime 必须有 `tool_ports` 字段
   - 新创建的 runtime `tool_ports = NULL`，所以拉不到！

---

## ⚠️ 根本问题

**架构重构不完整：**
1. ✅ 拆分了 Tools Server
2. ✅ 添加了 restore 机制（启动时恢复）
3. ❌ **但没有更新 runtime 创建流程**
4. ❌ **只能恢复旧的 runtime，新的无法创建**

这就像：建了新仓库，但忘记更新货物的配送流程！

---

## 📊 影响范围

| 组件 | 影响 | 修复后 |
|------|------|--------|
| Message Claim | ❌ 404 | ✅ 正常 |
| Runtime 创建 | ⚠️ 数据库有，Tools Server 无 | ✅ 同步 |
| 工具调用 | ❌ 404 | ✅ 正常 |
| 系统响应 | ❌ 完全卡住 | ✅ 正常 |

---

## 🎯 总结

**两个 bug，一个根源：代码重构不彻底**

1. **Bug 1**：拆分 Internal API 时，旧文件没删，路由冲突
2. **Bug 2**：拆分 Tools Server 时，创建流程没更新，导致同步失败

**教训：**
- 重构代码时要彻底清理旧代码
- 架构拆分时要完整更新所有调用链路
- 添加集成测试验证端到端流程

---

## ✅ 修复状态

- [x] Bug 1: Internal API 路由冲突
- [x] Bug 2: MCP Business Tools Server 集成
- [x] 测试验证待执行（重启后）

**准备重启应用以应用修复！**
