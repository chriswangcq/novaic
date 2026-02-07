# 端口持久化 - 快速参考

## 修改的文件

### 核心修改

1. **`novaic-backend/gateway/config/agents_db.py`**
   - ✅ 删除 `VmConfig.agent_index` 字段
   - ✅ 修改 `create_agent()` - 使用新的端口分配逻辑
   - ✅ 添加 `_allocate_new_ports()` - 智能端口分配
   - ✅ 修改 `list_agents()` - 向后兼容旧数据
   - ✅ 修改 `get_agent()` - 向后兼容旧数据

2. **`novaic-backend/gateway/db/repositories/agent.py`**
   - ✅ 删除 `get_used_agent_indices()` 方法
   - ✅ 删除 `find_next_agent_index()` 方法

### 已适配（无需修改）

- `novaic-backend/gateway/vm/manager.py` - 已使用 `agent.vm.ports`
- `novaic-backend/gateway/api/internal.py` - 已使用 `agent.vm.ports`

## 关键变化

### 之前：动态计算端口

```python
# 创建时
agent_index = find_next_agent_index()  # 找到下一个 index
vm_config["agent_index"] = agent_index

# 运行时
ports = allocate_ports_for_agent(agent.vm.agent_index)  # 重新计算
```

### 现在：持久化端口

```python
# 创建时
ports = _allocate_new_ports()  # 查询已用端口，分配新端口
vm_config["ports"] = ports  # 直接保存端口配置

# 运行时
ports = agent.vm.ports  # 直接读取，无需计算
```

## 端口分配逻辑

### 新的分配策略

```python
def _allocate_new_ports(self) -> PortConfig:
    # 1. 获取所有已存在的 agent
    all_agents = self.repo.list_agents()
    
    # 2. 收集已使用的 SSH 端口
    used_ssh_ports = set()
    for agent in all_agents:
        if ports and "ssh" in ports:
            used_ssh_ports.add(ports["ssh"])
        elif "agent_index" in vm_config:  # 兼容旧数据
            ssh_port = BASE_PORT + agent_index * PORTS_PER_AGENT + SERVICE_OFFSETS["ssh"]
            used_ssh_ports.add(ssh_port)
    
    # 3. 找到下一个可用的端口范围
    index = 0
    while True:
        ssh_port = BASE_PORT + index * PORTS_PER_AGENT + SERVICE_OFFSETS["ssh"]
        if ssh_port not in used_ssh_ports:
            break
        index += 1
    
    # 4. 分配完整的端口配置
    return allocate_ports_for_agent(index)
```

### 端口范围示例

```
Agent 0: SSH=20008, VNC=20006, WebSocket=20007
Agent 1: SSH=20028, VNC=20026, WebSocket=20027
Agent 2: SSH=20048, VNC=20046, WebSocket=20047
...
```

每个 agent 占用 20 个端口（PORTS_PER_AGENT=20）

## 向后兼容

### 旧数据格式

```json
{
  "vm_config": {
    "agent_index": 2,
    ...
  },
  "ports": {}  // 空
}
```

### 读取时自动转换

```python
# 在 list_agents() 和 get_agent() 中
if not ports and "agent_index" in vm_config:
    # 自动从 agent_index 计算端口
    ports = allocate_ports_for_agent(agent_index).model_dump()

# 移除 agent_index（不暴露给外部）
vm_config.pop("agent_index", None)
```

### 转换后的格式

```json
{
  "vm_config": {
    // agent_index 已移除
    ...
  },
  "ports": {
    "ssh": 20048,
    "vnc": 20046,
    "websocket": 20047,
    ...
  }
}
```

## 测试结果

### ✅ 基本功能测试

- 创建 agent：端口正确分配
- 多个 agent：端口不冲突
- 删除后复用：端口可以被新 agent 使用
- 持久化：重新加载后端口一致
- 无 agent_index：`VmConfig` 不再包含此字段

### ✅ 向后兼容测试

- 旧数据读取：自动计算端口
- 端口计算正确：基于 agent_index
- 新旧不冲突：新 agent 避开旧端口
- 字段自动清理：agent_index 不暴露

## 使用示例

### 创建 Agent

```python
from gateway.config.agents_db import get_agent_config_manager

manager = get_agent_config_manager()

# 创建 agent（端口自动分配并持久化）
agent = manager.create_agent(
    name="my-agent",
    os_type="ubuntu",
    os_version="24.04"
)

# 直接访问端口配置
print(f"SSH Port: {agent.vm.ports.ssh}")
print(f"VNC Port: {agent.vm.ports.vnc}")
```

### 读取 Agent

```python
# 获取 agent
agent = manager.get_agent(agent_id)

# 端口配置已持久化，直接使用
ports = agent.vm.ports
print(f"SSH: {ports.ssh}")
print(f"VNC: {ports.vnc}")
print(f"WebSocket: {ports.websocket}")

# agent_index 不再存在
# agent.vm.agent_index  # ❌ AttributeError
```

### VM 启动

```python
from gateway.vm import get_vm_manager

# VM Manager 会从 agent 配置中读取端口
manager = get_vm_manager()
result = manager.start(
    agent_id=agent_id,
    memory="4096",
    cpus=4
)

# 不再需要传递 agent_index ✅
```

## 保留的函数

以下函数保留用于内部使用和向后兼容：

```python
# 在 agents_db.py 中
def get_agent_port(agent_index: int, service: str) -> int:
    """计算特定服务的端口（内部使用）"""
    ...

def allocate_ports_for_agent(agent_index: int) -> PortConfig:
    """基于索引分配端口（内部使用）"""
    ...
```

**用途**:
1. `_allocate_new_ports()` 内部调用
2. 向后兼容旧数据计算端口

## 迁移清单

### 自动处理（无需操作）

- ✅ 旧 agent 自动兼容
- ✅ 端口自动计算
- ✅ agent_index 自动隐藏

### 可选的显式迁移

如果想将所有旧数据转换为新格式：

```python
# 参考 PORT_PERSISTENCE_REFACTOR_SUMMARY.md 中的迁移脚本
# 这是可选的，系统已经支持自动兼容
```

## 关键要点

1. **端口持久化**: 创建时分配，保存到数据库
2. **无需计算**: 运行时直接读取，不再计算
3. **向后兼容**: 旧数据自动转换，无缝升级
4. **智能分配**: 自动检测已用端口，避免冲突
5. **端口复用**: 删除 agent 后端口可立即复用

---

**状态**: ✅ 已完成并测试  
**版本**: 2026-02-06
