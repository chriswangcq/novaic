# PR-31  `*_state_transitions` 日志表（持久化转移历史）

| 字段 | 值 |
| --- | --- |
| **Phase** | 5 |
| **Milestone** | M4 |
| **承诺** | R8 |
| **Status** | `[x]` |
| **Depends on** | PR-28, PR-29, PR-21 |
| **Blocks** | — |
| **估时** | 1 d |
| **Owner** | 2026-04-15 |
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

---

## 落地实现（2026-04-15）

### 存储分布

| 机器 | 位置 | 写入时机 | 读取入口 |
| --- | --- | --- | --- |
| **message** | Entangled SQL `message_state_transitions` 表 | `message_state.transition` 内部，co-transactional（`transaction("global")` 同块内 INSERT，和 `UPDATE chat_messages` 原子提交） | `GET /v1/state_transitions/message/{id}` / `GET /internal/messages/{id}/trace` 里的 `history[]` |
| **subagent** | Entangled SQL `subagent_state_transitions` 表 | Business `subagent_state.transition` 成功 `store.update` 后，POST `/v1/state_transitions/subagent` （best-effort，失败仅 WARN 不 rollback） | `GET /v1/state_transitions/subagent/{id}` / `GET /internal/subagents/{agent_id}/{subagent_id}/state-history` |
| **scope** | Cortex 本机 NDJSON 追加文件（默认 `~/.novaic/cortex/scope_state_transitions.ndjson`，`CORTEX_SCOPE_STATE_LOG` 覆盖） | `scope_state.transition` 在 meta.json 更新成功后 append | `GET /v1/scope/history?scope_path=...&limit=...` |

Scope 侧选 NDJSON 而非 sqlite：Cortex 不依赖 Entangled，引入 HTTP/SQL 都是新的 coupling；NDJSON POSIX append 已是崩溃安全的写法，量级（每次对话几行）完全够用。跨主机聚合留给 sidecar（tail + 远送），不在本 PR 范围。

### 幂等与静默

- **self-loop 不写日志**。这是从 PR-23 / PR-29 延伸的不变式：订阅者/recovery 重试会触发 A→A 幂等路径，若 log 每次都写，一个 stuck message 就能淹没整张表。测试 `test_message_transition_noop_does_not_log` / `test_self_loop_does_not_log` / `test_self_loop_noop_skips_history_log` 把它钉住。
- **子代理 log POST 失败不 rollback**。`subagents.status` 已经先写了，这时 Entangled 500 也不该让业务面看到假失败——用 `try/except` 吞下，WARN 一行。测试 `test_transition_swallows_log_hook_errors` 覆盖。
- **message log 共事务**。因为它本来就在 Entangled 内部，能塞进同一个 `transaction("global")` 里，就正好不必容忍断档。

### 新文件

- `Entangled/packages/server-python/entangled/sql/state_transitions.py` — 两张表的 schema + reader/writer。
- `Entangled/packages/server-python/entangled/app/state_transitions.py` — FastAPI router（POST/subagent、GET/subagent、GET/message）。
- `Entangled/packages/server-python/tests/test_state_transitions.py` — 10 条用例。
- `novaic-cortex/novaic_cortex/scope_state_log.py` — NDJSON 读写。
- `novaic-cortex/tests/test_scope_state_log.py` — 9 条用例。

### 修改点

- `Entangled/.../sql/message_state.py`：`transition` 内 `INSERT INTO message_state_transitions`（co-tx）。
- `Entangled/.../sql/entity_store.py::ensure_all_schemas`：调用 `ensure_state_transitions_schema(db)`。
- `Entangled/.../app/factory.py`：注册 `state_transitions_router`。
- `novaic-common/common/entangled_client.py`：新增 `record_subagent_transition` / `history_*`。
- `novaic-business/business/internal/subagent_state.py`：`_record_transition` 后置 HTTP 上报。
- `novaic-business/business/internal/subagent.py`：新增 `GET /subagents/{agent_id}/{subagent_id}/state-history`。
- `novaic-business/business/internal/message.py`：`/internal/messages/{id}/trace` 的响应新增 `history[]`（soft-fail）。
- `novaic-cortex/novaic_cortex/scope_state.py`：`transition` 成功后 `await append_transition(...)`。
- `novaic-cortex/novaic_cortex/api.py`：新增 `GET /v1/scope/history`。

### 验收

```bash
# Entangled 本地
cd Entangled/packages/server-python
pytest tests/test_state_transitions.py tests/test_message_state.py
# 10 + 26 passed

# Cortex 本地
cd ../../../novaic-cortex
pytest tests/test_scope_state.py tests/test_scope_state_log.py
# 15 + 9 passed

# Business 本地
cd ../novaic-business
pytest tests/test_subagent_state.py
# 25 passed（含 PR-31 新增的 3 条 hook 用例）
```

### 后续可做

- **PR-31b**（可选）：把 `record_subagent_transition` 改成同步 in-Entangled 路径——如果 Business 的幂等 state 写入迁移到 Entangled 侧，顺带合入。
- **PR-31c**（可选）：metric emitter (PR-26) 改读 `*_state_transitions` 表，消除 "日志 grep + 表查询" 两条并行事件源。
