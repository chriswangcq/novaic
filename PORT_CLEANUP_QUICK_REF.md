# 端口配置清理 - 快速参考

## 修改概览

### 🎯 目标
只保留 SSH 端口，删除所有 MCP、VNC、WebSocket 相关端口。

### 📊 端口数量变化
- **之前**: 20 个端口/Agent (20000-21999 共 2000 个)
- **之后**: 1 个端口/Agent (20000-20099 共 100 个)
- **减少**: 95% 端口占用

---

## 修改的文件

### 1. `gateway/config/agents.py`
```python
# PortConfig - 只保留 SSH
class PortConfig(BaseModel):
    ssh: int = 20000  # ✅ 唯一保留的端口

# 常量更新
PORTS_PER_AGENT = 1  # 20 → 1
SERVICE_OFFSETS = {
    "ssh": 0,  # 只保留 SSH
}

# VmConfig - 删除 mcp_vm_port
class VmConfig(BaseModel):
    # ... 其他字段 ...
    ports: PortConfig = Field(default_factory=PortConfig)
    # ❌ 删除: mcp_vm_port: int = 8080
```

### 2. `gateway/config/agents_db.py`
```python
# 同样的修改
PORTS_PER_AGENT = 1
SERVICE_OFFSETS = {"ssh": 0}

class PortConfig(BaseModel):
    ssh: int = 20000

class VmConfig(BaseModel):
    # ... 其他字段 ...
    ports: PortConfig = Field(default_factory=PortConfig)
    # ❌ 删除: mcp_vm_port
```

### 3. `gateway/vm/manager.py`
```python
# VmConfig - 删除 mcp_vm_port
@dataclass
class VmConfig:
    agent_id: str
    ports: PortConfig
    memory: str = "4096"
    cpus: int = 4
    image_path: Optional[str] = None
    # ❌ 删除: mcp_vm_port: int = 8080

# 端口检查 - 只检查 SSH
# ❌ 删除: for port_name in ["ssh", "vm"]
# ✅ 改为: if self._is_port_in_use(config.ports.ssh)

# QEMU 端口转发 - 只转发 SSH
port_forward = f"hostfwd=tcp::{ports.ssh}-:22"
# ❌ 删除: f"hostfwd=tcp:127.0.0.1:{ports.vm}-:{config.mcp_vm_port}"

# 启动流程 - 删除 MCP 等待
# ❌ 删除: self._wait_for_service(ports.vm, "MCP", ...)

# 状态返回 - MCP 相关设为空
mcp_healthy=False,  # 不再使用
mcp_url="",  # 不再使用
```

### 4. `gateway/api/internal.py`
```python
# API 返回 - 只返回 SSH 端口
return {
    "ports": {"ssh": ports.ssh},  # ✅ 只返回 SSH
    # ❌ 删除: "vnc": ports.vnc, "websocket": ports.websocket
}
```

---

## 删除的端口

| 端口名 | 之前端口号 | 用途 | 状态 |
|--------|-----------|------|------|
| vm | 20000 | VM 内 MCP 服务 | ❌ 已删除 |
| session | 20001 | 会话管理 MCP | ❌ 已删除 |
| local | 20002 | 本地文件 MCP | ❌ 已删除 |
| memory | 20003 | 记忆管理 MCP | ❌ 已删除 |
| chat | 20004 | 用户通信 MCP | ❌ 已删除 |
| qemudebug | 20005 | QEMU 调试 MCP | ❌ 已删除 |
| vnc | 20006 | VNC 显示 | ❌ 已删除 |
| websocket | 20007 | WebSocket | ❌ 已删除 |
| **ssh** | **20000** | **SSH 访问** | **✅ 保留** |

---

## 端口分配示例

### 新的端口分配
```
Agent 0: ssh=20000
Agent 1: ssh=20001
Agent 2: ssh=20002
...
Agent 99: ssh=20099
```

### 之前的端口分配（已废弃）
```
Agent 0: 20000-20019 (20个端口)
  - vm=20000, session=20001, ..., ssh=20006
Agent 1: 20020-20039 (20个端口)
  - vm=20020, session=20021, ..., ssh=20026
```

---

## 验证清单

### ✅ 完成项目
- [x] 简化 `PortConfig` (agents.py 和 agents_db.py)
- [x] 删除 `mcp_vm_port` 字段
- [x] 更新 `PORTS_PER_AGENT` (20 → 1)
- [x] 简化 `SERVICE_OFFSETS` (只保留 ssh)
- [x] 删除 VM 端口转发 (manager.py)
- [x] 删除 MCP 服务等待 (manager.py)
- [x] 简化端口检查逻辑 (manager.py)
- [x] 更新 API 返回值 (internal.py)
- [x] 验证无语法错误
- [x] 验证无残留引用

### ✅ 搜索验证
```bash
# 验证没有残留的端口引用
grep -rn "ports\.vm" gateway/  # 0 结果
grep -rn "ports\.vnc" gateway/  # 0 结果
grep -rn "ports\.websocket" gateway/  # 0 结果
grep -rn "mcp_vm_port" gateway/  # 0 结果
```

---

## 向后兼容性

### 数据库
- **已有 agents**: 配置不变，旧端口存在但不再使用
- **新 agents**: 只分配 SSH 端口

### API 客户端
客户端需要适配新的响应格式：
```python
# 之前
ports = response["ports"]
ssh_port = ports["ssh"]
vnc_port = ports["vnc"]  # ❌ 不再存在

# 之后
ports = response["ports"]
ssh_port = ports["ssh"]  # ✅ 只有这个
```

---

## 后续工作

### 建议检查的文件
1. **Frontend** (`novaic-app/`):
   - 检查使用端口信息的组件
   - 适配新的 API 响应格式

2. **测试脚本**:
   - 更新硬编码的端口号
   - 删除 MCP 端口相关测试

3. **文档**:
   - 更新架构文档
   - 更新部署指南

---

## 常见问题

### Q: 为什么只保留 SSH 端口？
A: 
- FastMCP (vmuse) 已删除，不需要 VM MCP 端口
- x11vnc + websockify 已删除，改用 vmcontrol + Unix socket
- SSH 用于 VM 部署和调试，仍然需要

### Q: 旧的 agents 怎么办？
A: 
- 数据库中保持原配置不变
- 代码会忽略不存在的端口字段
- 新创建的 agents 使用简化配置

### Q: 如何访问 VNC？
A: 
- 现在通过 vmcontrol service 的 WebSocket
- 路径: `ws://localhost:8080/api/vms/{agent_id}/vnc`
- 不再需要端口转发

### Q: 端口范围缩小会影响什么？
A: 
- 只影响新创建的 agents
- 端口分配更紧凑、更易管理
- 降低端口冲突风险

---

**参考**: 完整报告见 `PORT_CLEANUP_REPORT.md`
