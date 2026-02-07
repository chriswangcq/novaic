# 向后兼容代码移除总结

## 概述

已移除所有处理旧 `agent_index` 字段的向后兼容代码。系统不再支持旧数据格式，需要手工迁移数据库。

## 修改清单

### 1. 数据库层 - `novaic-backend/gateway/config/agents_db.py`

#### 1.1 简化端口分配逻辑

**`_allocate_new_ports()` 方法**：
- ✅ 移除了从 `agent_index` 计算端口的兼容代码
- ✅ 仅保留从数据库 `ports` 字段读取端口的逻辑
- 修改前：检查 `ports` 字段和 `agent_index` 字段
- 修改后：只检查 `ports` 字段

#### 1.2 简化 `list_agents()` 方法

- ✅ 移除了 `agent_index` 字段的检查和计算
- ✅ 移除了删除 `agent_index` 字段的代码
- 修改前：如果没有 `ports` 但有 `agent_index`，则计算端口
- 修改后：直接使用 `ports` 字段，不做兼容处理

#### 1.3 简化 `get_agent()` 方法

- ✅ 移除了 `agent_index` 字段的检查和计算
- ✅ 移除了删除 `agent_index` 字段的代码
- 修改前：如果没有 `ports` 但有 `agent_index`，则计算端口
- 修改后：直接使用 `ports` 字段，不做兼容处理

#### 1.4 更新注释

**`get_agent_port()` 函数**：
- ✅ 添加注释说明仅用于创建 agent 时的内部使用
- ✅ 明确运行时应使用数据库中的端口配置

**`allocate_ports_for_agent()` 函数**：
- ✅ 添加注释说明仅用于创建 agent 时的内部使用
- ✅ 明确不应在运行时调用此函数

### 2. API 层 - `novaic-backend/gateway/api/internal.py`

#### 2.1 删除 DEPRECATED 端点

- ✅ 删除 `GET /config/ports/{agent_index}` 端点（标记为 DEPRECATED 的）
- ✅ 只保留 `GET /config/ports/by-agent/{agent_id}` 端点
- 删除了约 30 行代码（包括端点函数及其注释）

### 3. 配置模块 - `novaic-backend/gateway/config/agents.py`

#### 3.1 更新端口分配函数注释

**`get_agent_port()` 函数**：
- ✅ 添加注释说明仅用于创建 agent 时的内部使用
- ✅ 明确运行时应使用数据库中的端口配置

**`allocate_ports_for_agent()` 函数**：
- ✅ 添加注释说明仅用于创建 agent 时的内部使用
- ✅ 明确不应在运行时调用此函数

#### 3.2 清理注释

- ✅ 将 "Re-export for backward compatibility" 改为 "Public exports"

### 4. VM Manager - `novaic-backend/gateway/vm/manager.py`

- ✅ 验证错误信息不包含"可能需要迁移"等兼容性提示
- 当前错误信息已足够简洁：`"Agent {agent_id} not found or has no port configuration"`

### 5. 文档清理

- ✅ 移除 `agents_db.py` 中的 "Alias for Backward Compatibility" 改为 "Alias"
- ✅ 移除 `agents.py` 中的 "Re-export for backward compatibility" 改为 "Public exports"

## 未修改的文件

以下文件包含"兼容"字样但无需修改：

1. **`gateway/clients/vmuse_adapter.py`**
   - 保留：该文件本身就是适配器，其目的是提供兼容层
   - 说明："提供向后兼容的接口" 是该适配器的核心功能

2. **其他文档文件**
   - 保留：各种 DEPRECATED 标记的文档仅用于记录历史，不影响代码运行

## 验证要点

### 数据库需求

系统现在要求所有 agent 必须在数据库中包含完整的 `ports` 配置：

```json
{
  "ports": {
    "vm": 20000,
    "session": 20001,
    "local": 20002,
    "memory": 20003,
    "chat": 20004,
    "qemudebug": 20005,
    "vnc": 20006,
    "websocket": 20007,
    "ssh": 20008
  }
}
```

### 运行时行为

- ✅ 创建新 agent 时：自动分配端口并存储到数据库
- ✅ 查询 agent 时：直接从数据库读取端口配置
- ❌ 不再支持：从 `agent_index` 字段计算端口
- ❌ 不再支持：自动迁移旧数据

### API 变更

- ✅ 移除端点：`GET /config/ports/{agent_index}`
- ✅ 保留端点：`GET /config/ports/by-agent/{agent_id}`

## 数据迁移建议

如果数据库中还有旧格式的 agent（包含 `agent_index` 但没有 `ports`），需要手工迁移：

```python
# 伪代码：迁移脚本
from gateway.config.agents import allocate_ports_for_agent

for agent in old_agents:
    if "agent_index" in agent["vm_config"] and not agent.get("ports"):
        agent_index = agent["vm_config"]["agent_index"]
        ports = allocate_ports_for_agent(agent_index)
        
        # 更新数据库
        repo.update_agent(
            agent_id=agent["id"],
            ports=ports.model_dump()
        )
        
        # 删除 agent_index 字段
        del agent["vm_config"]["agent_index"]
```

## 测试建议

1. **创建新 agent**：验证端口自动分配
2. **查询 agent**：验证端口配置正确返回
3. **启动 VM**：验证使用正确的端口配置
4. **API 测试**：验证旧端点 `/config/ports/{agent_index}` 已移除

## 影响范围

- **数据库层**：不再支持 `agent_index` 字段
- **API 层**：移除基于 `agent_index` 的端点
- **运行时**：所有端口配置必须来自数据库
- **文档**：清理了向后兼容相关注释

## 总结

✅ 所有向后兼容代码已成功移除
✅ 系统现在完全依赖数据库中的端口配置
✅ 端口分配函数仅用于创建新 agent
✅ 需要手工迁移旧数据（如果存在）

---

**清理完成日期**: 2026-02-06
**修改文件数量**: 4
**删除代码行数**: ~50 行
**添加注释行数**: ~20 行
