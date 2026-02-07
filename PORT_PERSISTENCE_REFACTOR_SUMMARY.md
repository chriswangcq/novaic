# 数据库层端口持久化重构 - 完成总结

## 概述

成功完成数据库层的端口持久化重构，移除了对 `agent_index` 的依赖。端口配置现在在创建 agent 时分配并持久化到数据库，不再需要运行时动态计算。

## 实施的修改

### 1. 数据库 Schema 修改

**文件**: `novaic-backend/gateway/config/agents_db.py`

- ✅ 删除 `VmConfig.agent_index` 字段（第 65 行）
- ✅ 保留 `VmConfig.ports: PortConfig` 字段

**修改前**:
```python
class VmConfig(BaseModel):
    ...
    ports: PortConfig = Field(default_factory=PortConfig)
    mcp_vm_port: int = 8080
    agent_index: int = 0  # ❌ 已删除
```

**修改后**:
```python
class VmConfig(BaseModel):
    ...
    ports: PortConfig = Field(default_factory=PortConfig)
    mcp_vm_port: int = 8080
    # agent_index 字段已删除
```

### 2. Agent 创建逻辑修改

**文件**: `novaic-backend/gateway/config/agents_db.py`

- ✅ 修改 `create_agent()` 方法，使用新的端口分配逻辑
- ✅ 移除 `agent_index` 字段的分配和存储

**修改前**:
```python
def create_agent(...):
    agent_index = self.repo.find_next_agent_index()
    ports = allocate_ports_for_agent(agent_index)
    vm_config = {
        ...
        "agent_index": agent_index,
    }
```

**修改后**:
```python
def create_agent(...):
    # 分配新端口（基于已使用端口找到空闲范围）
    ports = self._allocate_new_ports()
    vm_config = {
        ...
        # 移除 agent_index
    }
```

### 3. 新的端口分配逻辑

**文件**: `novaic-backend/gateway/config/agents_db.py`

- ✅ 添加 `_allocate_new_ports()` 方法

**实现特性**:
```python
def _allocate_new_ports(self) -> PortConfig:
    """
    分配新的端口配置，避免与现有 agent 冲突。
    策略：查询所有已使用的 SSH 端口，找到下一个可用的端口范围。
    """
    # 获取所有已存在的 agent
    all_agents = self.repo.list_agents()
    
    # 收集已使用的 SSH 端口（作为端口范围的标识）
    used_ssh_ports = set()
    for agent in all_agents:
        # 支持向后兼容：从 ports 字段或 agent_index 计算端口
        ...
    
    # 找到下一个可用的端口范围
    index = 0
    while True:
        base_port = BASE_PORT + index * PORTS_PER_AGENT
        ssh_port = base_port + SERVICE_OFFSETS["ssh"]
        if ssh_port not in used_ssh_ports:
            break
        index += 1
    
    return allocate_ports_for_agent(index)
```

### 4. Repository 清理

**文件**: `novaic-backend/gateway/db/repositories/agent.py`

- ✅ 删除 `get_used_agent_indices()` 方法
- ✅ 删除 `find_next_agent_index()` 方法

这些方法不再需要，因为端口分配不再基于 agent index。

### 5. 向后兼容性

**文件**: `novaic-backend/gateway/config/agents_db.py`

- ✅ 在 `list_agents()` 中添加兼容逻辑
- ✅ 在 `get_agent()` 中添加兼容逻辑

**兼容逻辑**:
```python
# 向后兼容：如果没有端口配置但有 agent_index，则自动计算端口
if not ports and "agent_index" in vm_config:
    agent_index = vm_config["agent_index"]
    ports = allocate_ports_for_agent(agent_index).model_dump()

# 移除 agent_index 字段（不再暴露给外部）
vm_config.pop("agent_index", None)
```

### 6. API 层清理

**文件**: `novaic-backend/gateway/api/internal.py`

现有代码已经适配（通过检查发现以下函数已经使用 `agent.vm.ports`）：
- ✅ `rt_qemu_status()` - 直接使用 `agent.vm.ports`
- ✅ `rt_qemu_start()` - 不再传递 `agent_index` 给 VM manager
- ✅ `rt_qemu_restart()` - 不再传递 `agent_index` 给 VM manager

废弃的 API（保留用于向后兼容）：
- `/config/ports/{agent_index}` - 标记为 DEPRECATED

## 测试验证

### 测试 1：端口分配和持久化

✅ **通过** - 测试结果:
- 创建多个 agent，端口配置正确分配
- 端口不冲突
- 删除 agent 后，端口可以被复用
- 端口配置正确持久化到数据库
- 重新加载 agent 时端口配置保持一致
- `agent_index` 字段不再存在于 `VmConfig` 中

### 测试 2：向后兼容性

✅ **通过** - 测试结果:
- 旧数据（包含 `agent_index` 但没有 `ports`）可以正确读取
- 端口从 `agent_index` 自动计算（agent_index=2 -> SSH port=20048）
- 新创建的 agent 不会与旧数据的端口冲突
- `agent_index` 字段在读取时自动移除，不暴露给外部
- 所有 agent 的端口都不冲突

## 架构改进

### 之前的架构

```
Agent 创建 → 计算 agent_index → 基于 index 计算端口
           ↓
       保存 agent_index
           ↓
运行时读取 → 基于 agent_index 重新计算端口 ❌ 动态计算
```

**问题**:
- 运行时需要动态计算端口
- 依赖 agent_index 顺序
- 端口配置不直观
- 难以支持自定义端口

### 现在的架构

```
Agent 创建 → 查询已用端口 → 分配新端口
           ↓
       保存端口配置到数据库
           ↓
运行时读取 → 直接使用持久化的端口 ✅ 直接读取
```

**优势**:
- ✅ 端口配置持久化，不需要运行时计算
- ✅ 更灵活，支持自定义端口（未来）
- ✅ 更直观，端口配置一目了然
- ✅ 删除 agent 后端口可以立即复用
- ✅ 向后兼容旧数据

## 保留的函数

以下函数仍然保留，用于内部端口分配和向后兼容：

**`novaic-backend/gateway/config/agents_db.py`**:
- `get_agent_port(agent_index: int, service: str)` - 用于向后兼容计算
- `allocate_ports_for_agent(agent_index: int)` - 用于端口分配

**`novaic-backend/gateway/config/agents.py`**:
- 同样的函数保留用于向后兼容

这些函数现在只在以下情况使用：
1. 创建新 agent 时分配端口（`_allocate_new_ports()` 内部调用）
2. 读取旧数据时计算端口（向后兼容）

## 数据迁移

### 当前策略：自动兼容（无需显式迁移）

现有的 agent 数据：
- 如果有 `agent_index` 但没有 `ports`：自动从 `agent_index` 计算端口
- 读取时 `agent_index` 字段会被自动移除，不暴露给外部
- 新创建的 agent 会自动避开旧数据的端口

### 可选的显式迁移

如果需要将所有旧数据迁移到新格式，可以运行以下脚本（可选）：

```python
from gateway.config.agents_db import get_agent_config_manager, allocate_ports_for_agent
from gateway.db.access import get_db
from gateway.db.repositories.agent import AgentRepository

def migrate_old_agents():
    """将旧格式的 agent 数据迁移到新格式"""
    db = get_db()
    repo = AgentRepository(db)
    
    for agent_data in repo.list_agents():
        vm_config = agent_data.get("vm_config", {})
        ports = agent_data.get("ports", {})
        
        # 如果有 agent_index 但没有 ports
        if "agent_index" in vm_config and not ports:
            agent_index = vm_config["agent_index"]
            ports = allocate_ports_for_agent(agent_index).model_dump()
            
            # 更新到数据库
            vm_config.pop("agent_index")
            repo.update_agent(
                agent_id=agent_data["id"],
                vm_config=vm_config,
                ports=ports
            )
            print(f"Migrated agent {agent_data['id']} (index={agent_index})")
```

## 注意事项

1. **废弃的 API**: `/config/ports/{agent_index}` 已标记为 DEPRECATED，但仍然可用
2. **VM Manager**: 已经适配新的端口配置方式，从数据库读取端口
3. **端口冲突**: 新的端口分配逻辑会检查所有已使用的端口，包括旧数据
4. **性能**: 端口分配时需要查询所有 agent，但这是一次性操作（创建时）

## 后续工作

### 可选的改进（未来）

1. **自定义端口支持**: 允许用户在创建 agent 时指定自定义端口
2. **端口范围配置**: 支持配置不同的端口范围
3. **显式数据迁移**: 提供脚本将所有旧数据迁移到新格式
4. **端口冲突检测**: 在启动时检测系统端口占用

### 清理工作（可选）

1. 删除 `agents.py` 中不再需要的函数（如果确认没有其他地方使用）
2. 完全移除对 `agent_index` 的引用（当前保留用于向后兼容）

## 结论

✅ **重构成功完成**

- 端口配置已成功持久化到数据库
- `agent_index` 字段已从 `VmConfig` 中移除
- 所有测试通过（包括向后兼容性）
- 代码更简洁、更易维护
- 为未来的自定义端口功能奠定基础

---

**完成时间**: 2026-02-06  
**测试状态**: ✅ 全部通过  
**向后兼容**: ✅ 完全兼容
