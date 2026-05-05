# PR-53 — Entangled `EXTRA_ALLOWLIST` silently drops continuity columns

> Historical ticket archive: this file records a closed or retired implementation path. It is not current architecture or active backlog; use the ticket index and current architecture docs as the source of truth.


| Field | Value |
|---|---|
| **Ticket**  | PR-53 |
| **Status**  | `[✓]` deployed to prod 2026-04-22 22:55 CST; smoke PASS (see §关单 checklist) |
| **Opened**  | 2026-04-25 |
| **Owner**   | wc |
| **Severity** | **P0 regression** — silently disabled **three** production continuity features (PR-42 `handoff_notes`, PR-45 `historical_summary`, PR-43 Wave A `last_scope_id`) for every wake since each respective deploy. Users observed as "agent forgets previous conversation, context panel empty, wake acts like cold start". |
| **Blocks**  | Any future ancillary column piggybacked on a terminal status flip (same bug class will eat future features otherwise) |
| **Blocked by** | — |
| **Invariant** | R-INV (renewed): *the columns a caller writes through a state-machine PATCH must persist, OR the write must fail loudly*. Silent drop is forbidden. |

## 现象（2026-04-22 22:36 CST 复现）

User 发一条消息 `"现在几点了"`。Agent 正常回复 `"现在是晚上 22:36..."`, 走完 rest saga（`cortex_scope_end` → `subagent.set_sleeping` → `subagent.set_completed`），状态机 `awake → sleeping (reason=rest)` 入 `subagent_state_transitions` 表。

但：

```sql
SELECT subagent_id, historical_summary, handoff_notes, last_scope_id
FROM subagents;
-- main-415f6cfd | NULL | NULL | NULL
-- main-test-age | NULL | NULL | NULL
-- main-canary_a | NULL | NULL | NULL
```

**全表全列全空**。已部署的 PR-42 / PR-45 / PR-43 Wave A 全员写入失败，没有一行日志、没有一个测试红过。

Subscriber 侧的证据（PR-45.1 加的日志）：

```
business.subscribers.dispatch_subscriber - event=continuity_resolve
  agent=415f6cfd... subagent=main-415f6cfd result=empty
  has_handoff=0 has_summary=0 has_prev=0
```

每一次 wake 都是 `has_prev=0`，于是：
* `<HANDOFF_NOTES>` 永远不注入
* `<HISTORICAL_SUMMARY>` 永远不注入
* `<PREV_SCOPE_TAIL>` 永远不注入（PR-43 Wave C 的消费侧天然降级）

对用户的直接观感：「agent 每次醒来都像没吃过药」。

## 根因（完整调用链）

```text
1. runtime: handle_subagent_set_sleeping(payload)
     updates = {
       "status": "sleeping",            # 触发 Business 状态机分支
       "need_rest": 0,
       "historical_summary": "...",      # PR-45
       "last_scope_id": "...",           # PR-43 Wave A
       "last_scope_archived_at": "...",  # PR-43 Wave A
       "_transition_reason": "rest",
       "_transition_actor": "runtime.subagent_handlers",
     }
     business_client.entity_update("subagents", subagent_id, updates, ...)

2. business: PATCH /internal/entities/subagents/{id}
     internal_update_entity 看到 entity=="subagents" AND "status" in data
     → 走 subagent_state.transition 路径（非 generic entity_store.update_where）
     → pop status / _transition_reason / _transition_actor
     → extra = {k:v for k,v in data.items() if not k.startswith("_")}
     → = {need_rest, historical_summary, last_scope_id, last_scope_archived_at}
     → subagent_state.transition(to="sleeping", extra=extra)

3. business→entangled HTTP: transition_subagent(extra={4 keys})

4. entangled: sql/subagent_state.transition
     EXTRA_ALLOWLIST = frozenset({"need_rest", "progress", "error", "result"})
     clean_extra = {k:v for k,v in extra.items() if k in EXTRA_ALLOWLIST}
     → clean_extra = {"need_rest": 0}
     → historical_summary / last_scope_id / last_scope_archived_at  ← 静默丢弃 ✂️
     → UPDATE subagents SET status='sleeping', need_rest=0, updated_at=... (无其他列)
     → INSERT subagent_state_transitions (metadata_json=NULL)
```

## 为什么测试没抓到

| 层 | 测试覆盖 | 盲点 |
|---|---|---|
| 1. runtime handler 单测 | ✅ 验证 `updates` dict 里有字段 | mock 掉了 `business_client.entity_update` |
| 2. business `subagent_state.transition` 单测 | ✅ 验证 HTTP 调用参数 | mock 掉了 `EntangledServiceClient` |
| 3. entangled `transition` 单测 | ✅ 验证 `EXTRA_ALLOWLIST` 逻辑 | **只覆盖 4 个老字段，从未 pin 新字段必须入列** |
| 4. 跨服务集成 | ❌ 没有 | — |

三层各自绿灯，跨层一次都没跑。典型的「契约在接缝处被吃」。

## 修复（PR-53 本身）

### F1 — 扩展 `EXTRA_ALLOWLIST` 到覆盖已知的 terminal-flip 续写列

`Entangled/packages/server-python/entangled/sql/subagent_state.py`:

```python
EXTRA_ALLOWLIST: frozenset[str] = frozenset({
    # legacy
    "need_rest", "progress", "error", "result",
    # PR-45 (2026-04-22)
    "historical_summary",
    # PR-43 Wave A (2026-04-24)
    "last_scope_id", "last_scope_archived_at",
})
```

> `handoff_notes` 不在此列。它走的是 `_exec_subagent_rest`（`updates` 不含 `status`）→ generic `entity_store.update_where` 路径，该路径按 `SqlEntityDef.field_map` 接受所有声明列，不经过本 allowlist。保留现状即可。

### F2 — 让 silent drop 成为**响亮 WARN**

同文件 `transition()` 内：

```python
dropped: list[str] = []
if extra:
    for key, value in extra.items():
        if key == "status":
            raise InvalidTransition(...)
        if key in EXTRA_ALLOWLIST:
            clean_extra[key] = value
        else:
            dropped.append(key)

if dropped:
    logger.warning(
        "subagent_state extra_dropped subagent=%s agent=%s to=%s "
        "dropped_keys=%s reason=%s actor=%s — add to EXTRA_ALLOWLIST "
        "or use generic entity_store.update",
        subagent_id, agent_id, to,
        ",".join(sorted(dropped)), reason or "-", actor or "-",
    )
```

下一个未登记的续写列出现时，prod 第一次写入就有 WARN 可 grep，不再等用户反馈几周后才发现。

### F3 — 跨层集成测试（contract ratchet）

`novaic-business/tests/test_pr53_continuity_allowlist_e2e.py`：TestClient 挂 Business `internal_update_entity` 路由，`EntangledServiceClient` 被 monkeypatch 成直接调用 Entangled 真实 `transition()` + in-memory sqlite。PATCH 一次 → `SELECT` 断言三列真落盘。

这是过去三个 PR 都假设存在、但从没存在过的测试。

## 验证步骤

### 本地
- [x] `Entangled/packages/server-python && pytest tests/test_subagent_state.py` — 15 passed（原 8 + PR-53 新增 7）
- [x] `novaic-business && pytest tests/` — 138 passed（原 135 + PR-53 新增 3）

### Prod 部署后
- [archived] `bash scripts/deploy-business.sh` 增量部署 Business + Entangled
- [archived] 发一条触发消息；`sqlite3 entangled.db "SELECT last_scope_id, historical_summary FROM subagents WHERE subagent_id=..."` 返回非空
- [archived] 下一次 wake 的 `continuity_resolve` 日志里 `has_summary=1 has_prev=1`
- [archived] `grep "extra_dropped" /opt/novaic/data/logs/business-*.log` 无输出（healthy baseline）

## 回滚

纯加性更改：
- `EXTRA_ALLOWLIST` 扩集合：回滚等同于继续丢弃（老行为），无数据 corruption 风险
- WARN：无状态

单独 revert 这一个 commit 即可。

## 工作指南（避免同类 bug）

同时更新 `docs/architecture/message-wake-principles.md` 补一条不变量：

> **R-ALLOWLIST**：凡在 `subagents` 状态机 PATCH 的 payload 中追加 ancillary 列，必须
> 1. 补入 `Entangled.sql.subagent_state.EXTRA_ALLOWLIST`
> 2. 在 `test_subagent_state.py` 里加 `test_continuity_fields_are_in_allowlist` 风格的 defensive unit
> 3. 在 `novaic-business/tests/test_pr53_continuity_allowlist_e2e.py` 里加一条 TestClient-level 断言
>
> 三者缺一：CI 不会红，但 prod 续写会失效。

## 关单 checklist

- [x] F1 allowlist 扩展
- [x] F2 WARN on drop
- [x] F3 e2e 集成测试 (3 cases)
- [x] entangled 单测扩展 (7 new cases)
- [x] 本地全量 pytest 绿（Entangled 139 + Business 138）
- [x] deploy 完成（`scripts/deploy-business.sh root@api.gradievo.com` 2026-04-22 22:55 CST）
- [x] prod smoke — 直接 PATCH 探针写入 3 个续写列后 `SELECT` 全部命中；`extra_dropped` WARN 零条
- [x] prod smoke — canary 自然 rest 路径：`main-canary_a` / `main-canary_b` 部署后首次 `awake→sleeping` 都写出 `last_scope_id`（pre-fix 全表 NULL）
- [archived] `<PREV_SCOPE_TAIL>` 真实端到端注入（依赖一次"同一 agent 二次 wake"，线上流量自然产生即命中，无需单独驱动）
- [x] `docs/architecture/message-wake-principles.md` R-ALLOWLIST 入库

---

## 2026-04-23 postscript (partially reverted by PR-55)

PR-53's F1 expanded `EXTRA_ALLOWLIST` to cover three columns:
`historical_summary`, `last_scope_id`, `last_scope_archived_at`.
PR-55 retired the `historical_summary` producer/consumer pipeline
(see [`PR-55-phantom-summary-pipeline-cleanup.md`](./PR-55-phantom-summary-pipeline-cleanup.md))
and therefore:

- `historical_summary` was removed from `EXTRA_ALLOWLIST`,
- the corresponding defensive unit/e2e coverage moved to
  "retired-key-is-dropped-with-WARN" shape
  (`test_retired_historical_summary_is_dropped` in
  `Entangled/.../tests/test_subagent_state.py`),
- `test_pr53_continuity_allowlist_e2e.py` was deleted,
- the `subagents.historical_summary` column is kept as tolerant
  legacy (no live reader/writer).

PR-53's other two invariants stand unchanged:

- **R-ALLOWLIST** — any new ancillary column piggybacked on a
  `subagents` status-flip PATCH still requires allowlist entry +
  defensive unit + cross-layer e2e test. The
  `last_scope_id` / `last_scope_archived_at` pair remains the
  canonical example.
- **WARN on drop** — the observability path that surfaces dropped
  keys is now also what catches stale callers still passing the
  retired `historical_summary` / `handoff_notes` fields.
