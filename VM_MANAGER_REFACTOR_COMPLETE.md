# VM Manager 重构完成报告

## 任务目标
将 VM Manager 从接收 `agent_index` 参数改为从 agent 配置中查询端口信息。

## 完成的修改

### 1. VmConfig 数据类修改
**文件**: `novaic-backend/gateway/vm/manager.py`

- ✅ 删除 `agent_index` 字段
- ✅ 添加 `agent_id` 必需字段
- ✅ 将 `ports` 改为必需字段（不再有默认值）

**修改前**:
```python
@dataclass
class VmConfig:
    memory: str = "4096"
    cpus: int = 4
    image_path: Optional[str] = None
    agent_index: int = 0
    ports: PortConfig = field(default_factory=lambda: allocate_ports_for_agent(0))
```

**修改后**:
```python
@dataclass
class VmConfig:
    agent_id: str
    ports: PortConfig  # 必需字段，从 agent 配置中获取
    memory: str = "4096"
    cpus: int = 4
    image_path: Optional[str] = None
```

### 2. start() 方法签名修改
**文件**: `novaic-backend/gateway/vm/manager.py`

- ✅ 删除 `agent_index` 参数
- ✅ 更新文档字符串

**修改前**:
```python
def start(
    self,
    agent_id: str,
    agent_index: int,
    memory: str = "4096",
    cpus: int = 4,
) -> Dict[str, Any]:
```

**修改后**:
```python
def start(
    self,
    agent_id: str,
    memory: str = "4096",
    cpus: int = 4,
) -> Dict[str, Any]:
    """
    Start VM for an agent.
    
    端口配置从 agent 配置中获取
    """
```

### 3. start() 方法实现修改
**文件**: `novaic-backend/gateway/vm/manager.py`

- ✅ 添加从数据库获取 agent 配置的逻辑
- ✅ 验证 agent 存在且有端口配置
- ✅ 使用持久化的端口配置创建 VmConfig

**核心逻辑**:
```python
# 从数据库获取 agent 配置
from gateway.config.agents_db import AgentConfigDbService
agent_service = AgentConfigDbService()
agent = agent_service.get(agent_id)

if not agent or not agent.vm or not agent.vm.ports:
    raise ValueError(f"Agent {agent_id} not found or has no port configuration")

logger.info(f"[VmManager] Starting VM for agent {agent_id} (ssh_port={agent.vm.ports.ssh})")

# Build config - 使用持久化的端口配置
config = VmConfig(
    agent_id=agent_id,
    ports=agent.vm.ports,
    memory=memory,
    cpus=cpus,
)
```

### 4. 日志输出修改
**文件**: `novaic-backend/gateway/vm/manager.py`

- ✅ 将日志从显示 `agent_index` 改为显示 `ssh_port`

**修改前**:
```python
logger.info(f"[VmManager] Starting VM for agent {agent_id} (index={agent_index})")
```

**修改后**:
```python
logger.info(f"[VmManager] Starting VM for agent {agent_id} (ssh_port={config.ports.ssh})")
```

### 5. 配置文件修改
**文件**: `novaic-backend/gateway/config/agents.py`

- ✅ 删除 VmConfig 中的 `agent_index` 字段
- ✅ 保留端口分配函数（仅用于内部计算和向后兼容）

**修改前**:
```python
class VmConfig(BaseModel):
    ...
    agent_index: int = 0       # Agent索引，用于端口分配
```

**修改后**:
```python
class VmConfig(BaseModel):
    ...
    # agent_index 字段已删除
```

### 6. Gateway 启动脚本修改
**文件**: `novaic-backend/main_gateway.py`

- ✅ 更新启动日志输出

**修改前**:
```python
print(f"[Gateway] Using ports from agent '{first_agent.name}' (index={first_agent.vm.agent_index})")
```

**修改后**:
```python
print(f"[Gateway] Using ports from agent '{first_agent.name}' (ssh={first_agent.vm.ports.ssh})")
```

### 7. API 层修改
**文件**: `novaic-backend/gateway/api/internal.py`

- ✅ 删除 `rt_qemu_start()` 中的 agent_index 获取逻辑
- ✅ 删除 `rt_qemu_restart()` 中的 agent_index 获取逻辑
- ✅ 更新所有 `manager.start()` 调用，移除 `agent_index` 参数

### 8. 测试脚本修改
**文件**: `novaic-backend/gateway/vm/test_guest_agent.py`

- ✅ 将参数从 `agent_index: int` 改为 `agent_id: str`
- ✅ 更新 socket 路径构建逻辑
- ✅ 更新错误消息和使用说明

**修改前**:
```python
def test_guest_agent(agent_index: int = 0):
    ga_socket_path = socket_dir / f"novaic-ga-{agent_index}.sock"
```

**修改后**:
```python
def test_guest_agent(agent_id: str):
    ga_socket_path = socket_dir / f"novaic-ga-{agent_id}.sock"
```

### 9. 文档更新
**文件**: `novaic-backend/gateway/vm/GUEST_AGENT_SETUP.md`

- ✅ 更新所有 agent_index 引用为 agent_id
- ✅ 更新 socket 路径示例
- ✅ 更新测试命令示例

## 向后兼容性

保留的功能（用于向后兼容）：

1. **端口分配函数** (`gateway/config/agents.py`):
   - `get_agent_port(agent_index, service)` - 仅用于内部计算
   - `allocate_ports_for_agent(agent_index)` - 仅在创建新 agent 时调用

2. **数据库兼容层** (`gateway/config/agents_db.py`):
   - 自动从旧的 `agent_index` 字段计算端口配置
   - 在读取时自动转换并移除 `agent_index` 字段

3. **API 端点** (`gateway/api/internal.py`):
   - `/config/ports/{agent_index}` - 标记为 DEPRECATED，保留用于向后兼容

## 依赖关系

VM Manager 现在依赖于：
- `gateway.config.agents_db.AgentConfigDbService` - 用于查询 agent 配置

## 错误处理

增强的错误处理：
- 如果 agent 不存在，抛出 `ValueError` 并包含清晰的错误信息
- 如果 agent 没有端口配置，抛出 `ValueError` 并包含清晰的错误信息

## 测试建议

1. **功能测试**:
   ```bash
   # 测试启动 VM
   curl -X POST http://localhost:19999/api/vm/start \
     -H "Content-Type: application/json" \
     -d '{"agent_id": "<agent_id>"}'
   
   # 测试 Guest Agent 连接
   cd novaic-backend/gateway/vm
   python test_guest_agent.py <agent_id>
   ```

2. **向后兼容测试**:
   - 测试包含旧 `agent_index` 字段的数据库记录是否能正常加载
   - 验证自动转换为端口配置是否正确

3. **错误处理测试**:
   - 测试使用不存在的 agent_id 启动 VM
   - 测试使用没有端口配置的 agent

## 注意事项

1. **循环依赖**: VM Manager 导入 `AgentConfigDbService` 是安全的，因为它们在不同的模块中
2. **端口冲突**: 端口分配逻辑仍然使用 agent_index 计算，确保与现有系统兼容
3. **日志一致性**: 所有日志现在使用 SSH 端口而不是 agent_index 来标识 agent

## 文件变更统计

```
novaic-backend/gateway/api/internal.py  | 356 ++++++++++----------------------
novaic-backend/gateway/config/agents.py |  28 +--
novaic-backend/gateway/vm/manager.py    | 118 ++++++++---
novaic-backend/main_gateway.py          |  14 +-
novaic-backend/gateway/vm/test_guest_agent.py | 修改完成
novaic-backend/gateway/vm/GUEST_AGENT_SETUP.md | 修改完成
```

## 完成状态

✅ 所有计划的修改都已完成
✅ 向后兼容性已保留
✅ 错误处理已增强
✅ 文档已更新
✅ 测试脚本已更新

## 下一步建议

1. 运行完整的集成测试
2. 验证所有 API 端点正常工作
3. 测试 VM 启动/停止流程
4. 验证 Guest Agent 连接功能
5. 更新相关的用户文档或 API 文档
