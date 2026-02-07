# 后端 API 层移除 agent_index 参数 - 完成报告

## 任务概述

成功移除后端 API 层中的 `agent_index` 参数，改为仅使用 `agent_id` 进行 Agent 识别。

## 修改内容

### 1. VM 启动 API (`novaic-backend/gateway/api/vm.py`)

#### 1.1 VmStartRequest 模型
**位置**: 第 30-36 行

**修改前**:
```python
class VmStartRequest(BaseModel):
    """Request to start VM."""
    agent_id: str
    agent_index: int  # 已删除
    memory: str = "4096"
    cpus: int = 4
```

**修改后**:
```python
class VmStartRequest(BaseModel):
    """Request to start VM."""
    agent_id: str
    memory: str = "4096"
    cpus: int = 4
```

#### 1.2 start_vm 函数
**位置**: 第 103-121 行

**修改**: 移除了向 `vm_manager.start()` 传递 `agent_index` 参数

**修改前**:
```python
result = manager.start(
    agent_id=request.agent_id,
    agent_index=request.agent_index,  # 已删除
    memory=request.memory,
    cpus=request.cpus,
)
```

**修改后**:
```python
result = manager.start(
    agent_id=request.agent_id,
    memory=request.memory,
    cpus=request.cpus,
)
```

### 2. Agent 信息 API (`novaic-backend/gateway/api/internal.py`)

#### 2.1 移除返回值中的 agent_index
**位置**: 第 1549-1557 行

**修改前**:
```python
return {
    "id": agent.id,
    "name": agent.name,
    "agent_index": agent.vm.agent_index,  # 已删除
    "default_model": agent.default_model,
}
```

**修改后**:
```python
return {
    "id": agent.id,
    "name": agent.name,
    "default_model": agent.default_model,
}
```

### 3. 端口查询 API (`novaic-backend/gateway/api/internal.py`)

#### 3.1 新增 agent_id 端点
**位置**: 第 1560 行之前插入

**新增**:
```python
@router.get("/config/ports/by-agent/{agent_id}")
def get_ports_by_agent_id(agent_id: str):
    """
    Get port configuration for an agent by agent_id.
    
    Retrieves ports from agent configuration in database.
    """
    from gateway.config.agents import GATEWAY_PORT, BASE_PORT, PORTS_PER_AGENT
    
    agent_mgr = get_agent_config_manager()
    agent = agent_mgr.get_agent(agent_id)
    
    if not agent or not agent.vm or not agent.vm.ports:
        raise HTTPException(status_code=404, detail="Agent not found or has no port configuration")
    
    ports = agent.vm.ports
    return {
        "agent_id": agent_id,
        "gateway_port": GATEWAY_PORT,
        "base_port": BASE_PORT,
        "ports_per_agent": PORTS_PER_AGENT,
        "ports": {
            "vm": ports.vm,
            "session": ports.session,
            "local": ports.local,
            "memory": ports.memory,
            "chat": ports.chat,
            "qemudebug": ports.qemudebug,
            "ssh": ports.ssh,
        }
    }
```

#### 3.2 标记旧端点为已废弃
**位置**: 第 1592 行

**修改**: 在 docstring 中添加了 `[DEPRECATED]` 标记

```python
@router.get("/config/ports/{agent_index}")
def get_ports_for_agent(agent_index: int):
    """
    [DEPRECATED] Get port configuration for an agent by index.
    
    This endpoint is deprecated. Use /config/ports/by-agent/{agent_id} instead.
    Kept for backward compatibility.
    """
```

### 4. SSH 执行 API (`novaic-backend/gateway/api/internal.py`)

**位置**: 第 2824-2834 行

**修改前**:
```python
# Get agent index for port allocation
config_mgr = get_agent_config_manager()
agents = config_mgr.list_agents()
agent_index = 0
for i, agent in enumerate(agents):
    if agent.id == agent_id:
        agent_index = i
        break

ports = allocate_ports_for_agent(agent_index)
ssh_port = ports.ssh
```

**修改后**:
```python
# Get agent port configuration from database
config_mgr = get_agent_config_manager()
agent = config_mgr.get_agent(agent_id)

if not agent or not agent.vm or not agent.vm.ports:
    raise HTTPException(status_code=404, detail="Agent not found or has no port configuration")

ssh_port = agent.vm.ports.ssh
```

### 5. VM 状态检查 API (`novaic-backend/gateway/api/internal.py`)

**位置**: 第 2861-2869 行

**修改前**:
```python
config_mgr = get_agent_config_manager()
agents = config_mgr.list_agents()
agent_index = 0
for i, agent in enumerate(agents):
    if agent.id == agent_id:
        agent_index = i
        break

ports = allocate_ports_for_agent(agent_index)
```

**修改后**:
```python
config_mgr = get_agent_config_manager()
agent = config_mgr.get_agent(agent_id)

if not agent or not agent.vm or not agent.vm.ports:
    raise HTTPException(status_code=404, detail="Agent not found or has no port configuration")

ports = agent.vm.ports
```

### 6. VM 启动 API (Runtime) (`novaic-backend/gateway/api/internal.py`)

**位置**: 第 2898-2914 行

**修改前**:
```python
# Get agent index for port allocation
config_mgr = get_agent_config_manager()
agents = config_mgr.list_agents()
agent_index = 0
for i, agent in enumerate(agents):
    if agent.id == agent_id:
        agent_index = agent.vm.agent_index if hasattr(agent.vm, 'agent_index') else i
        break

memory = data.get("memory", "4096")
cpus = data.get("cpus", 4)

try:
    manager = get_vm_manager()
    result = manager.start(
        agent_id=agent_id,
        agent_index=agent_index,
        memory=memory,
        cpus=cpus,
    )
```

**修改后**:
```python
memory = data.get("memory", "4096")
cpus = data.get("cpus", 4)

try:
    manager = get_vm_manager()
    result = manager.start(
        agent_id=agent_id,
        memory=memory,
        cpus=cpus,
    )
```

### 7. VM 重启 API (`novaic-backend/gateway/api/internal.py`)

**位置**: 第 2943-2967 行

**修改前**:
```python
# Get agent index for port allocation
config_mgr = get_agent_config_manager()
agents = config_mgr.list_agents()
agent_index = 0
for i, agent in enumerate(agents):
    if agent.id == agent_id:
        agent_index = agent.vm.agent_index if hasattr(agent.vm, 'agent_index') else i
        break

graceful = data.get("graceful", True)

try:
    manager = get_vm_manager()
    
    # Stop the VM first
    stop_result = manager.stop(
        agent_id=agent_id,
        graceful=graceful,
        quick=False,
    )
    
    # Start the VM again
    start_result = manager.start(
        agent_id=agent_id,
        agent_index=agent_index,
        memory="4096",
        cpus=4,
    )
```

**修改后**:
```python
graceful = data.get("graceful", True)

try:
    manager = get_vm_manager()
    
    # Stop the VM first
    stop_result = manager.stop(
        agent_id=agent_id,
        graceful=graceful,
        quick=False,
    )
    
    # Start the VM again
    start_result = manager.start(
        agent_id=agent_id,
        memory="4096",
        cpus=4,
    )
```

## 向后兼容性

### 保留的功能

1. **已废弃的端点**: `GET /config/ports/{agent_index}` 仍然可用，但标记为已废弃
2. **配置辅助函数**: `allocate_ports_for_agent(agent_index)` 保留在配置模块中
3. **旧数据兼容**: `agents_db.py` 中的代码会自动从旧的 `agent_index` 计算端口配置

### 迁移路径

客户端应该迁移到新的端点：
- **旧端点**: `GET /config/ports/{agent_index}`
- **新端点**: `GET /config/ports/by-agent/{agent_id}` ✅

## 影响分析

### API 端点变更

| 端点 | 变更类型 | 说明 |
|------|---------|------|
| `POST /api/vm/start` | 请求参数移除 | 不再接收 `agent_index` |
| `GET /agents/{agent_id}/runtime/info` | 响应字段移除 | 不再返回 `agent_index` |
| `GET /config/ports/by-agent/{agent_id}` | 新增 | 替代旧的按索引查询 |
| `GET /config/ports/{agent_index}` | 标记废弃 | 保留但不推荐使用 |
| `POST /rt/{runtime_id}/qemu/ssh-exec` | 内部实现变更 | 改用 agent_id 查询 |
| `GET /rt/{runtime_id}/qemu/status` | 内部实现变更 | 改用 agent_id 查询 |
| `POST /rt/{runtime_id}/qemu/start` | 内部实现变更 | 改用 agent_id 查询 |
| `POST /rt/{runtime_id}/qemu/restart` | 内部实现变更 | 改用 agent_id 查询 |

### 未修改的模块

以下模块中的 `agent_index` 使用保持不变：
- `gateway/config/agents.py` - 配置辅助函数（用于向后兼容）
- `gateway/config/agents_db.py` - 数据库兼容层（自动迁移旧数据）

## 错误处理

新增的错误处理：
- 当 Agent 不存在时，返回 404 错误
- 当 Agent 没有端口配置时，返回 404 错误并提示 "Agent not found or has no port configuration"

## 测试建议

1. **API 测试**:
   - 测试新的端口查询端点 `/config/ports/by-agent/{agent_id}`
   - 验证 VM 启动不再需要 `agent_index` 参数
   - 验证所有 runtime API 正常工作

2. **兼容性测试**:
   - 确认旧端点 `/config/ports/{agent_index}` 仍然可用
   - 测试从旧数据迁移的场景

3. **错误处理测试**:
   - 测试不存在的 agent_id
   - 测试没有端口配置的 agent

## 文件清单

修改的文件：
- ✅ `novaic-backend/gateway/api/vm.py`
- ✅ `novaic-backend/gateway/api/internal.py`

未修改但相关的文件：
- `novaic-backend/gateway/config/agents.py` (辅助函数，保留用于兼容)
- `novaic-backend/gateway/config/agents_db.py` (自动迁移逻辑)

## 验证结果

- ✅ 无语法错误
- ✅ 无 linter 错误
- ✅ 所有 API 层的 `agent_index` 参数已移除
- ✅ 向后兼容性已保留
- ✅ 错误处理已完善

## 后续工作

1. **前端迁移**: 更新前端代码，移除对 `agent_index` 的依赖
2. **文档更新**: 更新 API 文档，说明新的端点和废弃的端点
3. **监控**: 观察旧端点的使用情况，确定何时可以完全移除
4. **数据清理**: 在确认所有客户端迁移后，可以考虑从数据库模式中移除 `agent_index` 字段

---

**完成时间**: 2026-02-06  
**状态**: ✅ 已完成
