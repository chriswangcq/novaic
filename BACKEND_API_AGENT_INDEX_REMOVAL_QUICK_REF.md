# 后端 API 移除 agent_index - 快速参考

## 核心变更

### ✅ 已移除

| 位置 | 移除内容 |
|------|---------|
| `VmStartRequest` | `agent_index: int` 字段 |
| `vm_manager.start()` | `agent_index` 参数 |
| Agent 信息返回值 | `"agent_index"` 字段 |
| 所有内部索引查找循环 | `for i, agent in enumerate(agents)` 逻辑 |

### ✅ 新增

| 端点 | 说明 |
|------|------|
| `GET /config/ports/by-agent/{agent_id}` | 通过 agent_id 查询端口配置 |

### ⚠️ 已废弃（保留兼容）

| 端点 | 替代方案 |
|------|---------|
| `GET /config/ports/{agent_index}` | 使用 `/config/ports/by-agent/{agent_id}` |

## API 迁移指南

### 启动 VM

**旧方式**:
```json
POST /api/vm/start
{
  "agent_id": "agent-123",
  "agent_index": 0,
  "memory": "4096",
  "cpus": 4
}
```

**新方式**:
```json
POST /api/vm/start
{
  "agent_id": "agent-123",
  "memory": "4096",
  "cpus": 4
}
```

### 查询端口配置

**旧方式**:
```bash
GET /config/ports/0
```

**新方式**:
```bash
GET /config/ports/by-agent/agent-123
```

## 实现模式变更

### 获取端口配置

**旧模式**:
```python
# ❌ 不再使用
agents = config_mgr.list_agents()
agent_index = 0
for i, agent in enumerate(agents):
    if agent.id == agent_id:
        agent_index = i
        break
ports = allocate_ports_for_agent(agent_index)
```

**新模式**:
```python
# ✅ 推荐使用
agent = config_mgr.get_agent(agent_id)
if not agent or not agent.vm or not agent.vm.ports:
    raise HTTPException(404, "Agent not found or has no port configuration")
ports = agent.vm.ports
```

## 修改文件

- `novaic-backend/gateway/api/vm.py` (2 处修改)
- `novaic-backend/gateway/api/internal.py` (7 处修改)

## 验证清单

- [x] VM 启动 API 移除 `agent_index`
- [x] Agent 信息返回值移除 `agent_index`
- [x] 新增 agent_id 端口查询端点
- [x] SSH 执行改用 agent 配置
- [x] VM 状态检查改用 agent 配置
- [x] VM 启动（Runtime）改用 agent 配置
- [x] VM 重启改用 agent 配置
- [x] 无 linter 错误
- [x] 保留向后兼容性

## 注意事项

1. **向后兼容**: 旧的 `/config/ports/{agent_index}` 端点保留
2. **数据迁移**: `agents_db.py` 自动处理旧数据
3. **错误处理**: 新增 404 错误提示
4. **配置模块**: `allocate_ports_for_agent()` 函数保留用于兼容

---

**状态**: ✅ 完成  
**验证**: ✅ 通过  
**文档**: `BACKEND_API_AGENT_INDEX_REMOVAL_SUMMARY.md`
