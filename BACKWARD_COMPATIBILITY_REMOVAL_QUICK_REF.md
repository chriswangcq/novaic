# 向后兼容代码移除 - 快速参考

## 修改的文件

### 1. `novaic-backend/gateway/config/agents_db.py`

```python
# ✅ 简化了三个方法，移除 agent_index 兼容逻辑：

def _allocate_new_ports(self) -> PortConfig:
    # 移除：agent_index 计算端口
    # 保留：仅从 ports 字段读取

def list_agents(self) -> List[AICAgent]:
    # 移除：if not ports and "agent_index" in vm_config
    # 移除：vm_config.pop("agent_index", None)

def get_agent(self, agent_id: str) -> Optional[AICAgent]:
    # 移除：if not ports and "agent_index" in vm_config
    # 移除：vm_config.pop("agent_index", None)
```

### 2. `novaic-backend/gateway/api/internal.py`

```python
# ❌ 删除的端点：
@router.get("/config/ports/{agent_index}")  # 整个函数已删除

# ✅ 保留的端点：
@router.get("/config/ports/by-agent/{agent_id}")  # 继续使用
```

### 3. `novaic-backend/gateway/config/agents.py`

```python
# ✅ 添加注释说明仅用于创建 agent：

def get_agent_port(agent_index: int, service: str) -> int:
    """
    NOTE: This function is for internal use during agent creation only.
    Runtime code should use the port configuration stored in the database.
    """

def allocate_ports_for_agent(agent_index: int) -> PortConfig:
    """
    NOTE: This function is for internal use during agent creation only.
    """
```

## 关键变更

| 类别 | 修改前 | 修改后 |
|------|--------|--------|
| **端口获取** | 从 `ports` 或 `agent_index` 计算 | 仅从 `ports` 字段 |
| **API 端点** | 两个端点（index 和 id） | 一个端点（仅 id） |
| **错误处理** | "可能需要迁移" | 简洁错误信息 |
| **文档** | "向后兼容" | "内部使用" |

## 数据库要求

所有 agent 必须包含完整的 `ports` 配置：

```json
{
  "id": "xxx",
  "name": "My Agent",
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
  },
  "vm_config": {
    // ❌ 不再包含或使用 agent_index
  }
}
```

## 迁移检查清单

- [ ] 确认所有 agent 都有 `ports` 配置
- [ ] 确认没有代码依赖 `agent_index` 字段
- [ ] 确认前端不调用 `/config/ports/{agent_index}`
- [ ] 更新任何引用旧端点的文档

## 验证命令

```bash
# 检查是否还有 DEPRECATED 标记
rg "DEPRECATED.*agent_index" novaic-backend/

# 检查是否还有 agent_index 兼容代码
rg "if.*agent_index.*in.*vm_config" novaic-backend/gateway/config/

# 验证端点已删除
rg "@router.get.*config/ports/\{agent_index\}" novaic-backend/gateway/api/
```

## 回滚方案

如果需要回滚，可以：

1. 恢复 `agents_db.py` 中的三个方法
2. 恢复 `internal.py` 中的 DEPRECATED 端点
3. 使用 git revert 此次提交

---

**清理完成**: 2026-02-06  
**影响**: 数据库层、API 层、配置模块  
**测试**: 需要验证端口配置和 API 调用
