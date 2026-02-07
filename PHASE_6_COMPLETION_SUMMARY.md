# Phase 6 完成总结：移除 FastMCP 依赖

## 📋 变更概览

本次变更完成了 Phase 6 的核心目标：**移除 VMUSE 的 FastMCP 依赖，改用 vmcontrol 提供的 HTTP API**。

### 时间线
- **初始问题**: VNC 连接失败
- **根本原因**: Unix Socket 路径过长（134 字节 > 104 字节限制）
- **连带发现**: VM 工具无法被 Tools Server 发现
- **最终解决**: 修复 socket 路径 + 重构工具发现机制

---

## 🔄 完整变更流程

### 第一阶段：VNC 连接问题诊断与修复

#### 1. 问题表现
```
用户报告：vnc启动失败了
症状：noVNC 无法连接到 VM
```

#### 2. 诊断过程
- ✅ 检查 QEMU 进程 → 发现进程立即退出成为僵尸进程
- ✅ 检查 socket 文件 → 存在但无法连接
- ✅ 检查 QEMU 日志 → 发现 "UNIX socket path is too long" 错误
- ✅ 测量路径长度 → 134 字节（超出 104 字节限制）

#### 3. 修复方案
**文件**: `novaic-backend/gateway/vm/manager.py`

```python
# 修改前
socket_dir = Path(tempfile.gettempdir()) / "novaic"  # /var/folders/n3/.../T/novaic
# 路径: 134 字节

# 修改后
socket_dir = Path("/tmp/novaic")
# 路径: 70 字节 ✅
```

**涉及的 socket 文件**:
- `novaic-mcp-{agent_id}.sock`
- `novaic-qmp-{agent_id}.sock`
- `novaic-ga-{agent_id}.sock`
- `novaic-vnc-{agent_id}.sock`

#### 4. 额外修复
**QEMU 进程管理改进** (`gateway/vm/manager.py`)
- 将 stdout/stderr 从 PIPE 改为日志文件（防止缓冲区阻塞）
- 添加进程启动后的状态检查（及早发现失败）
- 日志位置：`~/Library/Application Support/com.novaic.app/logs/qemu-{agent_id}-stderr.log`

#### 5. 结果
✅ QEMU 进程稳定运行（PID 99429，运行 10+ 分钟）  
✅ VNC socket 正常创建  
✅ noVNC 连接成功  

---

### 第二阶段：VM 工具发现机制重构

#### 1. 问题表现
```
用户反馈：现在应该vm工具发现不了
原因：Phase 6 移除 FastMCP 后，工具发现机制未更新
```

#### 2. 架构原则（用户明确要求）
1. **Gateway 永远是被调用方** - 不主动推送，被动响应查询
2. **VM 工具不再通过 MCP 提供** - 改用 vmcontrol HTTP API
3. **集成 vmuse_adapter** - 使用适配器定义工具

#### 3. 旧架构（Phase 6 之前）
```
VM 内运行 FastMCP Server (端口 8080)
         ↓
Tools Server 通过 MCP 协议连接
         ↓
发现 VMUSE 提供的工具
```

#### 4. 新架构（Phase 6 之后）
```
Tools Server 发现工具时
         ↓
调用 Gateway API: GET /internal/runtimes/{runtime_id}/vm-tools
         ↓
Gateway 使用 vmuse_adapter.list_tools_mcp_format()
         ↓
返回 8 个 VM 工具定义
         ↓
Tools Server 合并到工具列表
```

#### 5. 实现细节

**文件 1**: `novaic-backend/gateway/api/internal.py` (+62 行)
```python
@router.get("/runtimes/{runtime_id}/vm-tools")
async def get_runtime_vm_tools(runtime_id: str):
    """
    获取 Runtime 的 VM 工具列表（用于 Tools Server 发现）
    """
    # 检查 Runtime 是否存在
    # 检查 Agent 是否有 VM 配置
    # 使用 vmuse_adapter 获取工具列表
    adapter = VmuseAdapter()
    tools = adapter.list_tools_mcp_format()
    return {"tools": tools, "agent_id": agent_id, "vm_available": True}
```

**文件 2**: `novaic-backend/gateway/clients/vmuse_adapter.py` (+103 行)
```python
def list_tools_mcp_format(self) -> List[Dict[str, Any]]:
    """返回 8 个 VM 工具的 MCP 格式定义"""
    return [
        # browser_navigate, browser_click, browser_type, browser_screenshot, browser_content
        # file_read, file_write
        # shell_exec
    ]
```

**文件 3**: `novaic-backend/tools_server/runtime_manager.py` (+30 行)
```python
async def _discover_tools(self, runtime_id: str, context: RuntimeContext):
    # ... 原有的 MCP 工具发现 ...
    
    # 新增：从 Gateway 获取 VM 工具
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{self._gateway_url}/internal/runtimes/{runtime_id}/vm-tools"
        )
        vm_tools = response.json().get("tools", [])
        tools.extend(vm_tools)  # 合并到工具列表
```

#### 6. VM 工具列表（8 个）
| 工具名 | 描述 | API 后端 |
|--------|------|----------|
| `browser_navigate` | 浏览器导航 | vmcontrol `/api/vms/{id}/browser/navigate` |
| `browser_click` | 点击元素 | vmcontrol `/api/vms/{id}/browser/click` |
| `browser_type` | 输入文本 | vmcontrol `/api/vms/{id}/browser/type` |
| `browser_screenshot` | 页面截图 | vmcontrol `/api/vms/{id}/browser/screenshot` |
| `browser_content` | 获取内容 | vmcontrol `/api/vms/{id}/browser/content` |
| `file_read` | 读取文件 | vmcontrol `/api/vms/{id}/guest/file` |
| `file_write` | 写入文件 | vmcontrol `/api/vms/{id}/guest/file` |
| `shell_exec` | 执行命令 | vmcontrol `/api/vms/{id}/guest/exec` |

---

## 🗑️ 需要清理的旧代码

### 1. FastMCP 相关（VM 内）

#### VM 镜像内的 FastMCP Server
**位置**: VM 内部（通过 Guest Agent 访问）
```bash
# 需要在 VM 内执行
systemctl stop vmuse-mcp.service  # 停止 FastMCP 服务
systemctl disable vmuse-mcp.service  # 禁用自启动
rm /etc/systemd/system/vmuse-mcp.service  # 删除服务文件
rm -rf /opt/vmuse/  # 删除 FastMCP 代码
```

#### Python 依赖清理
**位置**: VM 内部
```bash
pip3 uninstall fastmcp -y
```

### 2. Gateway 中的 MCP 端口转发

#### 端口配置清理
**文件**: `novaic-backend/gateway/config/agents.py`

查找并评估是否可以删除：
```python
# 可能需要删除的端口配置
ports.vm = xxx  # MCP 端口（如果只用于 FastMCP）
```

**注意**: 需要确认 `ports.vm` 是否还有其他用途！

### 3. QEMU 启动参数清理

#### MCP chardev 和 virtserialport
**文件**: `novaic-backend/gateway/vm/manager.py`

**当前代码**（约 548-551 行）:
```python
"-chardev", f"socket,id=mcp,path={socket_path},server=on,wait=off",
"-device", "virtserialport,chardev=mcp,name=mcp",
```

**是否删除**: ⚠️ **需要确认**
- 如果 MCP socket 只用于 FastMCP，可以删除
- 如果还有其他组件使用，需要保留
- 建议：先注释掉，测试后再删除

### 4. 健康检查逻辑

#### MCP 健康检查
**文件**: `novaic-backend/gateway/vm/manager.py`

**当前代码**（约 368 行）:
```python
mcp_healthy = self._is_port_in_use(ports.get("vm", 0))
```

**修改建议**:
```python
# 如果不再需要 MCP 端口检查，可以改为：
mcp_healthy = True  # 或直接删除该字段
```

### 5. 端口等待逻辑

#### 启动时等待 MCP 端口
**文件**: `novaic-backend/gateway/vm/manager.py`

**当前代码**（约 220 行）:
```python
# Wait for MCP
self._wait_for_service(ports.vm, "MCP", timeout=ServiceConfig.VM_MCP_TIMEOUT)
```

**修改建议**:
```python
# 删除该行，或改为等待 VM 内 Guest Agent 就绪
```

### 6. 配置常量清理

#### VM 超时配置
**文件**: `novaic-backend/common/config.py`

查找是否有 MCP 相关的超时配置：
```python
VM_MCP_TIMEOUT = xxx  # 可能可以删除
```

---

## 📝 清理优先级

### 🔴 高优先级（立即清理）
1. ✅ **VM 镜像内的 FastMCP Server** - 已不再使用，占用资源
2. ✅ **QEMU 启动参数中的 MCP chardev** - 如果确认不需要

### 🟡 中优先级（测试后清理）
3. ⚠️ **MCP 端口配置** - 需要确认是否还有其他用途
4. ⚠️ **MCP 健康检查逻辑** - 可以简化或删除
5. ⚠️ **端口等待逻辑** - 改为等待 Guest Agent

### 🟢 低优先级（可选清理）
6. ⚠️ **相关配置常量** - 代码整洁，非必需

---

## ✅ 测试验证清单

### Phase 6 功能验证
- [ ] VM 启动成功（QEMU 进程稳定运行）
- [ ] VNC 连接正常（noVNC 可以连接）
- [ ] Tools Server 能发现 8 个 VM 工具
- [ ] 工具调用正常（browser/file/shell 工具可用）
- [ ] vmcontrol API 响应正常

### 清理后验证
- [ ] VM 启动不依赖 FastMCP
- [ ] 删除 MCP chardev 后 VM 仍正常启动
- [ ] 工具发现仍然正常（不依赖 MCP 端口）
- [ ] 无相关错误日志

---

## 📂 关键文件清单

### 已修改的文件（本次变更）
```
novaic-backend/
├── gateway/
│   ├── vm/manager.py                    # Socket 路径 + QEMU 进程管理
│   ├── api/internal.py                  # VM 工具查询 API
│   └── clients/vmuse_adapter.py         # 工具列表定义
└── tools_server/
    └── runtime_manager.py               # 工具发现集成

novaic-app/
└── src-tauri/vmcontrol/
    └── src/api/routes/vnc.rs            # VNC WebSocket 代理（已支持短路径）
```

### 需要评估的文件（清理候选）
```
novaic-backend/
├── gateway/
│   ├── config/agents.py                 # 端口配置
│   └── vm/manager.py                    # MCP chardev 启动参数
└── common/config.py                     # 超时常量

VM 内部:
├── /etc/systemd/system/vmuse-mcp.service
├── /opt/vmuse/
└── FastMCP Python 包
```

---

## 🚀 部署步骤

1. **重启服务使修改生效**
   ```bash
   # 停止应用
   # 重新启动应用（会加载新代码）
   ```

2. **验证 VNC 连接**
   ```bash
   # 启动 VM
   curl -X POST http://localhost:19999/api/vm/start \
     -H "Content-Type: application/json" \
     -d '{"agent_id":"xxx","agent_index":1,"memory":"4096","cpus":4}'
   
   # 检查 socket
   ls -la /tmp/novaic/
   
   # 测试 noVNC 连接
   ```

3. **验证工具发现**
   ```bash
   # 查看 Tools Server 日志
   tail -f logs/tools_server.log | grep "VM tools"
   
   # 期望输出：
   # [RuntimeManager] Discovered 8 VM tools from Gateway for runtime: rt-xxx
   ```

4. **测试工具调用**
   ```python
   # 通过 Agent 调用 VM 工具
   # 验证 browser_navigate, file_read, shell_exec 等工具可用
   ```

---

## 📊 变更统计

### 代码变更
- **新增代码**: ~195 行
- **修改代码**: ~50 行
- **删除代码**: ~15 行
- **受影响文件**: 4 个核心文件

### 架构改进
- ✅ 移除 FastMCP 依赖
- ✅ 统一 VM 管理为 agent_id (UUID)
- ✅ 修复 Unix Socket 路径限制问题
- ✅ 改进 QEMU 进程管理
- ✅ 重构工具发现机制（Gateway 被动响应）

### 性能优化
- ✅ 减少 VM 内进程（FastMCP Server 可删除）
- ✅ 减少端口占用（MCP 端口可删除）
- ✅ 简化启动流程（无需等待 MCP 端口）

---

## 🎯 下一步行动

1. **立即行动**
   - 部署并测试当前修改
   - 验证 VNC 连接和工具发现

2. **短期计划**（1-2 天）
   - 清理 VM 镜像内的 FastMCP Server
   - 删除 QEMU 启动参数中的 MCP chardev
   - 简化健康检查逻辑

3. **长期优化**（按需）
   - 清理配置常量
   - 更新文档和注释
   - 创建清理后的 VM 镜像模板

---

## 📖 相关文档

- `PHASE_6_FASTMCP_REPLACEMENT_DESIGN.md` - Phase 6 设计文档
- `VM_TOOLS_DISCOVERY_IMPLEMENTATION.md` - 工具发现实现细节
- `VNC_WEBSOCKET_PROXY.md` - VNC 代理实现
- `VMUSE_MIGRATION_GUIDE.md` - FastMCP 迁移指南

---

**变更完成时间**: 2026-02-06  
**涉及 Phase**: Phase 6 (FastMCP Replacement)  
**状态**: ✅ 核心功能完成，待清理旧代码
