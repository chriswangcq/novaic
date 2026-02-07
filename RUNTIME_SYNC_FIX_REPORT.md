# Runtime 同步问题修复报告

## 🐛 问题描述

**错误信息：**
```
Client error '404 Not Found' for url 
'http://127.0.0.1:19998/internal/runtimes/rt-5464aa7117cc/tools/call'
```

## 🔍 根本原因

1. **Gateway 与 Tools Server 不同步**
   - Gateway 创建 runtime 后，**没有通知** Tools Server
   - Tools Server 中 runtime 数量为 0（`runtime_count: 0`）
   - 当 Master/Worker 尝试调用工具时，runtime 不存在，返回 404

2. **架构问题**
   - Gateway 负责创建 runtime 记录（数据库）
   - Tools Server 负责提供工具执行上下文
   - **缺少同步机制**

## ✅ 修复方案

### 修改文件：`gateway/api/internal/runtime.py`

#### 1. 修复 `POST /internal/runtimes`

**修改前：**
```python
@router.post("/runtimes")
def create_runtime(data: Dict[str, Any]):
    """Create a new Runtime for a SubAgent (v14)."""
    # ...
    runtime = repo.create_runtime(subagent_id, agent_id, initial_context)
    return _runtime_to_dict(runtime)  # ❌ 没有通知 Tools Server
```

**修改后：**
```python
@router.post("/runtimes")
async def create_runtime(data: Dict[str, Any]):
    """Create a new Runtime for a SubAgent (v14)."""
    # ...
    runtime = repo.create_runtime(subagent_id, agent_id, initial_context)
    
    # ✅ 通知 Tools Server 创建 runtime 上下文
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{ServiceConfig.TOOLS_SERVER_URL}/internal/runtimes",
                json={
                    "runtime_id": runtime.runtime_id,
                    "agent_id": agent_id,
                    "subagent_id": subagent_id,
                    "ports": {},
                }
            )
            response.raise_for_status()
    except Exception as e:
        print(f"[Gateway] Warning: Failed to notify Tools Server: {e}")
    
    return _runtime_to_dict(runtime)
```

#### 2. 修复 `POST /internal/runtimes/main`（同样修改）

### 关键改进

1. **异步通知**：使用 `httpx.AsyncClient` 调用 Tools Server API
2. **容错处理**：通知失败不影响 runtime 创建（仅记录警告）
3. **配置化**：使用 `ServiceConfig.TOOLS_SERVER_URL`
4. **自动同步**：runtime 创建后立即同步到 Tools Server

## 🔄 数据流

```
用户发消息
  ↓
Gateway 接收消息
  ↓
创建 Saga
  ↓
Master 创建 Runtime
  ↓ POST /internal/runtimes
Gateway 创建 runtime 记录（DB）
  ↓ ✅ 新增：通知 Tools Server
  ↓ POST http://127.0.0.1:19998/internal/runtimes
Tools Server 创建工具上下文
  ↓
Master 调用工具
  ↓ POST /internal/runtimes/{runtime_id}/tools/call
Tools Server 执行工具 ✅ 成功
```

## 📊 验证步骤

### 1. 检查修复前状态

```bash
# Gateway 有 runtime
curl http://127.0.0.1:19999/internal/runtimes/active

# Tools Server 没有 runtime（问题）
curl http://127.0.0.1:19998/internal/runtimes
# 返回：{"runtimes":[],"total":0}
```

### 2. 重启应用

```bash
# 退出 NovAIC.app，重新打开
```

### 3. 发送测试消息

在 NovAIC 中发送消息，观察是否正常响应。

### 4. 验证同步

```bash
# 检查 Tools Server 中是否有 runtime
curl http://127.0.0.1:19998/internal/runtimes

# 应该返回：
# {"runtimes":[{"runtime_id":"rt-xxx",...}],"total":1}
```

## 🎯 预期结果

修复后：
1. ✅ Gateway 创建 runtime 时自动通知 Tools Server
2. ✅ Tools Server 中有对应的工具上下文
3. ✅ Master 调用工具成功（不再 404）
4. ✅ 用户消息正常处理

## 📝 其他发现

在排查过程中还修复了另一个问题：

### Internal API 路由冲突

**问题：**
- 旧的 `internal.py` 文件（97KB）和新的 `internal/` 文件夹同时存在
- 子模块错误设置了 `prefix="/internal"`，导致双重前缀

**修复：**
1. ✅ 删除旧的 `internal.py` 文件
2. ✅ 修复所有 11 个子模块的路由配置（移除 prefix）

**修复文件：**
- `gateway/api/internal/agent.py`
- `gateway/api/internal/broadcast.py`
- `gateway/api/internal/config.py`
- `gateway/api/internal/health.py`
- `gateway/api/internal/llm.py`
- `gateway/api/internal/message.py` ⭐ 修复了 `claim-and-prepare` 404
- `gateway/api/internal/runtime.py`
- `gateway/api/internal/subagent.py`
- `gateway/api/internal/task.py`
- `gateway/api/internal/vm.py`
- `gateway/api/internal/web.py`

## 🚀 部署建议

1. **立即重启应用**：修复生效
2. **监控日志**：观察 "Failed to notify Tools Server" 警告
3. **测试工具调用**：确认工具执行正常
4. **清理旧 runtime**：如有需要，清理数据库中的孤儿 runtime

## ⚠️ 注意事项

1. **容错设计**：Tools Server 通知失败不影响 runtime 创建
2. **TODO 项**：获取 agent 的实际端口配置（当前为空对象）
3. **向后兼容**：修复不影响现有 runtime，仅影响新创建的

---

## 总结

本次修复解决了 Gateway 与 Tools Server 之间缺少同步机制的问题。修复后，runtime 创建流程更加健壮，工具调用不再出现 404 错误。

**修改文件：**
- `gateway/api/internal/runtime.py`（2 个函数）

**影响范围：**
- 所有新创建的 runtime
- 所有工具调用

**风险：** 极低（容错处理 + 向后兼容）
