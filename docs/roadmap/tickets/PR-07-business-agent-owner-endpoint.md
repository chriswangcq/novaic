# PR-07  Business `GET /internal/agents/{agent_id}/owner`

| 字段 | 值 |
| --- | --- |
| **Phase** | 1 |
| **Milestone** | M1 |
| **承诺** | R3 |
| **Status** | `[ ]` |
| **Depends on** | — |
| **Blocks** | PR-08 |
| **估时** | 0.5 d |
| **Owner** | __ |
| **PR 标题** | `feat(business): expose internal endpoint for agent owner lookup` |

## 目标

把"`agent_id → owner user_id`"做成唯一上游来源，为 `AgentOwnershipResolver` (PR-08) 和 `DispatchAssembler` (PR-10) 提供权威数据。

## 范围

- `novaic-business/business/internal/agents.py`（若不存在则创建）
- `novaic-business/main_business.py`（路由挂载）
- Entangled 侧：确认 `agents` / `subagents` 实体里确实存了 owner（通常是 `user_id`）

## 前置 Checklist

- [ ] 确认数据源：
  ```bash
  sqlite3 ~/.novaic/data/entangled.db "PRAGMA table_info(agents);"
  # 应有 user_id 字段
  ```
- [ ] 如没有 owner 字段 → 单独一个先导 PR 补 schema；本 PR 阻塞

## 实施 Checklist

### 路由

- [ ] `GET /internal/agents/{agent_id}/owner`
  - 200 `{"agent_id": "...", "user_id": "..."}`
  - 404 `{"error": "agent not found", "agent_id": "..."}`
  - 内部端点，走已有 internal auth（X-Internal-Key）

### 实现

```python
# business/internal/agents.py
router = APIRouter(prefix="/internal/agents", tags=["internal"])

@router.get("/{agent_id}/owner")
async def get_owner(agent_id: str, store: EntangledStore = Depends(...)):
    row = await store.get("agents", agent_id)
    if row is None:
        raise HTTPException(404, "agent not found")
    user_id = row.get("user_id") or row.get("owner_user_id")
    if not user_id:
        raise HTTPException(404, "agent has no owner")
    return {"agent_id": agent_id, "user_id": user_id}
```

- [ ] Handler 入口 log：`agent_owner_lookup agent_id=... user_id=... caller=<from X-Internal-Service>`

### 边界

- [ ] agent 存在但 `user_id IS NULL` → 400 vs 404 的语义选择：**404**（"no owner"），便于 resolver 统一抛 `AgentNotOwnedError`
- [ ] 同一 `agent_id` 不可能有两个 owner（DB 级约束已保证）；仅返回第一条

## 测试 Checklist

- [ ] 单测：
  - [ ] 正常 agent → 200 + user_id
  - [ ] 不存在 → 404
  - [ ] agent 存在但 user_id NULL → 404
- [ ] 集成：start Business + curl 内部端点

## 可观测性 Checklist

- [ ] metric `agent_owner_lookup_total{result=hit|miss}` counter
- [ ] log 带 `caller=`（依赖 PR-06）

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P1-3（第一半）→ `[x]`
- [ ] 本工单 Status → `[x]`
- [ ] [docs/cortex/internal-api-schemas.md](../../cortex/internal-api-schemas.md) 里补 Business 这条内部端点契约

## 验收命令

```bash
curl -H "X-Internal-Key: $NOVAIC_INTERNAL_KEY" \
     -H "X-Internal-Service: test" \
     http://localhost:8200/internal/agents/<agent_id>/owner
# 200: {"agent_id":"...","user_id":"..."}

curl -H "X-Internal-Key: $NOVAIC_INTERNAL_KEY" \
     -H "X-Internal-Service: test" \
     http://localhost:8200/internal/agents/nonexistent/owner
# 404
```

## 回滚

`git revert` — 纯新增端点，无现有调用方。

## 备注

- 若 owner 字段名在 schema 里是 `owner_user_id` 而非 `user_id`，在 handler 里做一次转换，统一对外为 `user_id`。Resolver (PR-08) 不需要关心 schema 命名。
