# PR-31  `*_state_transitions` 日志表（持久化转移历史）

| 字段 | 值 |
| --- | --- |
| **Phase** | 5 |
| **Milestone** | M4 |
| **承诺** | R8 |
| **Status** | `[ ]` |
| **Depends on** | PR-28, PR-29, PR-21 |
| **Blocks** | — |
| **估时** | 1 d |
| **Owner** | __ |
| **PR 标题** | `feat(observability): state_transitions log tables for subagent/scope/message` |

## 目标

把 `transition(...)` 的事件流持久化成可查表，便于事后回放 "这个实体的完整生命周期"。纯观测能力。

## 范围

- Entangled schema：新增 `subagent_state_transitions`、`message_state_transitions`
- Cortex 本地存储：`scope_state_transitions.sqlite` 或 append-only log 文件
- 对应 `transition()` 函数里写入逻辑

## 前置 Checklist

- [ ] PR-21 / PR-28 / PR-29 都已落地（transition 唯一入口）

## 实施 Checklist

### Schema

```sql
-- 模板（subagent_state_transitions、message_state_transitions 结构一致）
CREATE TABLE subagent_state_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,
    from_state TEXT NOT NULL,
    to_state TEXT NOT NULL,
    reason TEXT,
    actor TEXT,                    -- service_name / worker_id
    scope_id TEXT,                 -- 若相关
    metadata_json TEXT,
    created_at INTEGER NOT NULL
);
CREATE INDEX idx_sst_entity ON subagent_state_transitions (entity_id, created_at);
```

### Scope 侧（Cortex）

- [ ] 若 Cortex 独立于 Entangled DB，在 Cortex 的 `scope_locks` 相邻位置放 `scope_state.sqlite`（或追加 `events.ndjson`）
- [ ] 同步写：transition 成功后立即 append

### Transition 函数里写入

```python
def transition(store, entity_id, *, to, reason, actor, extra=None):
    # ... 原有逻辑
    store.execute("""
        INSERT INTO subagent_state_transitions
            (entity_id, from_state, to_state, reason, actor, metadata_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (entity_id, cur, to, reason, actor, json.dumps(extra or {}), now_ms))
```

### 查询端点 / CLI

- [ ] Business `GET /internal/subagents/{id}/history` → 返回 transition 列表
- [ ] Entangled 或 Business 暴露 `GET /internal/messages/{id}/history`
- [ ] Cortex `GET /v1/scope/{id}/history`

### 保留策略

- [ ] 日志表按 entity_id 建 index；默认无 TTL（运维按需清理）

## 测试 Checklist

- [ ] 单测：transition 写一行 log
- [ ] 集成：spawn → sleep → wake → archive → history 返回 4 条记录
- [ ] 集成：message pending → claimed → consumed → history 返回 2 条转移

## 可观测性 Checklist

- [ ] `GET /history` 端点有 metric
- [ ] 日志表 size 作为 DB 体积监控

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P5-3 → `[x]`
- [ ] 本工单 Status → `[x]`
- [ ] `docs/runbooks/troubleshooting.md` 加 "按 history 回放实体生命周期"

## 验收命令

```bash
sqlite3 ~/.novaic/data/entangled.db ".schema subagent_state_transitions"
# 存在
sqlite3 ~/.novaic/data/entangled.db \
  "SELECT entity_id, from_state, to_state, reason, actor FROM subagent_state_transitions ORDER BY id DESC LIMIT 5;"
```

## 回滚

`git revert` —— 删 INSERT 路径；表可保留作为空表。

## 备注

- 本 PR 完成后，"这个实体为什么还在 sleeping" 变成一次 history 查询。
- 未来可将 metric emitter（PR-26）改为从 history 表驱动，统一事件源。
