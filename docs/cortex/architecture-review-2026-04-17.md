# Architecture Review — 2026-04-17

> **历史评审归档**：本文记录 2026-04-17 当时的代码审查结论。当前主路径已迁移到 agent-root / wake scope / `skill_end(report=...)` / `wake_finalize`；文中的 `subagent_rest`、auto meta skill 等术语保留为当时上下文，不代表最新 Cortex 契约。
>
> 8 位架构师 subagent 并行评审 + 8 位 summarizer subagent 并行汇总后的定档卷宗。
>
> - 范围：`novaic-cortex`（状态真相）+ `novaic-agent-runtime`（无状态编排）。
> - 基线：已落地 P0–P4（auto_meta_skill 必选、`user_id` 必填、check_stack fail-safe、round cap 可配置、DFS auto-close、`_SKILL_LOCKS` + 归档清理）。
>
> 审查方法：8 位架构师只读访问代码（ripgrep + Read），分别从 State Consistency / Concurrency / Fault Tolerance / Control Flow / API Contract / Observability / Performance / Security 八个维度给出 verdict + findings + invariants。本文是定稿版本。
>
> 下一步执行计划见 `[hardening-checklist.md](./hardening-checklist.md)`。

## 0. 核实纠偏（bus factor note）

Architect #1 / #6 均指出「`react_think.py` / `subagent_rest.py` / `saga_worker_sync.py` / `health_worker_sync.py` 缺失，saga 会 mark_failed」。**实地核查为假警报** —— 四个文件均存在且正确 `register_saga_definition`，`saga_worker_sync.py:300-303` 显式枚举 4 个 saga_type。原因：两位架构师读取到了不完整的 workspace 快照。

其余发现已与本地代码一一对照，见下。

---

## Architect #1 — State & Consistency

**Verdict: Significant issues**

### [P0] ~~`react_think` / `subagent_rest` sagas referenced but NOT registered~~ — FALSE POSITIVE

- 实测 `sagas/__init__.py` 自动导入全部 4 个模块，`saga_worker_sync.py:300-303` 认识全部 4 类。

### [P1] Subagent `current_scope_id` is a second "scope pointer" outside Cortex

- Evidence: `task_queue/handlers/subagent_handlers.py:34-43` writes `current_scope_id` to entity; `business/schema_push.py:103-125` SUBAGENTS_DEF schema excerpt doesn't list that column.
- Impact: Drift risk vs Cortex stack; possible schema mismatch failure.
- Fix: Either formalize column as non-authoritative pointer or remove.

### [P1] `context.read` dual-writes Cortex + EntityStore without transaction

- Evidence: `task_queue/handlers/context_handlers.py:69-84` appends to Cortex then marks message read; crash between = duplicate or skew.
- Fix: Idempotent ingestion (dedup by message id in Cortex) or transactional outbox.

### [P2] `advance_round` is non-atomic RMW across two HTTP calls

- Evidence: `task_queue/utils/cortex_bridge.py:193-199` read meta + write meta.
- Impact: Lost updates under concurrent advances on same root scope.
- Fix: Cortex-side atomic increment endpoint.

### [P2] Cortex `append_context` has no idempotency key handling

- Evidence: `workspace.py:583-588` always appends; bridge attaches `_idempotency_key` but Cortex ignores.
- Fix: Dedup by `_idempotency_key` in Workspace, or document reliance on task idempotency.

### [P2] `react_actions` not transactional across tools + steps + stack check

- Evidence: `sagas/react_actions.py:177-190` parallel execute → parallel save → check_stack.
- Fix: Strong idempotency on tool.execute + step writes; optional per-round serialization.

### [P3] `get_cortex_bridge` cache keyed only by `scope_id`

- Evidence: `cortex_bridge.py:518-536` — composite key should include user/agent.

### [P3] Internal `/v1/internal/skill/begin|end` bypass `_SKILL_LOCKS`

- Evidence: `api.py:905-917` vs `409-418`; two skill API families with different locking.
- Fix: Deprecate internal skill path or add same locks.

---

## Architect #2 — Concurrency & Races

**Verdict: Significant issues (single-worker deploy is OK; multi-worker would break locks)**

### [High] Parallel `execute_tools` → concurrent `/v1/steps/write` races on `_index.jsonl`

- Evidence: `sagas/react_actions.py:177-185` parallel tool + parallel save; `api.py:632-643` `/v1/steps/write`; `workspace.py:427-465` `write_step` uses `_count_step_dirs` then `_sys_append_line` which is read-get-put (`workspace.py:120-126`); `store.py:3-6` documents unsafe for concurrent RMW on non-S3.
- Impact: Lost updates to `_index.jsonl`; duplicate `seq`/filename collisions; `resolve_active_scope_path` reads inconsistent view.
- Fix: Serialize step writes per root `scope_id` (extend `_SKILL_LOCKS` key or dedicated step lock), or atomic append at store level, or non-parallel `save_results` within a round.

### [Medium] `SessionRepository.dispatch` race — `INSERT OR IGNORE` loser still returns `saga_started`

- Evidence: `queue_service/session_repo.py:150-170` INSERT OR IGNORE without checking affected rows; always returns `saga_started` with new `scope_id` even when loser.
- Impact: Two concurrent dispatches → two sagas created; one loses race; caller sees "saga_started" for an orphaned `scope_id`.
- Fix: Check rowcount/lastrowid; return `deduped` / attach existing session.

### [Medium] `uvicorn --workers > 1` would break `_SKILL_LOCKS`

- Evidence: `novaic-cortex/novaic_cortex/main_cortex.py:69-74` `uvicorn.run` no `workers=`; `scripts/start.sh:154-163` single process.
- Fix: Keep single-worker, or distributed locking (Redis/DB), or LB tenant-affinity.

### [Low] Internal `/v1/internal/skill/`* bypass lock

### [Low] skill_begin duplicate child_scope_id rejects, not idempotent

### [Low] Wrong-order skill_end returns `ok: false` (correct — LIFO enforced)

---

## Architect #3 — Fault Tolerance & Recovery

**Verdict: Queue-level recovery is solid; Cortex writes intentionally "soft-fail" in bridge — risks silent truth loss**

### [High] `cortex_bridge.py` public methods catch all exceptions → return None/{}/[]

- Evidence: `_post` uses `raise_for_status()`; every public method (`create_scope` L92-108, `write_step` L291-306, `context_skill_begin` L450-462) swallows Exception into warning log + empty return.
- Fix: Structured error propagation; selective retry with backoff for idempotent reads; surface hard failures to saga for steps that must be durable.

### [High] `context_handlers.py` L115-122: `write_step` returns `success: True` even when `result is None`

- Fix: Treat `result is None` as failure.

### [Medium] `cortex_handlers.py:46-48` scope_end outer except returns `success: True` with `error`

### [Medium] `cortex_handlers.py:109-114` skill_end returns `success: True` on exception (asymmetry with skill_begin)

### [Medium] No second-line compensation if `subagent_rest` saga itself fails

- `queue_service/saga_repo.py:391-423` `mark_failed` enqueues `subagent_rest` for wake/think/actions, but not for `subagent_rest` itself.
- Fix: External watchdog + alert.

### [Low] check_stack fail-safe is conservative (intentional)

### [Info] Worker crash recovery OK; dispatch during Cortex outage OK; wake-path set_subagent_awake failure → compensation OK

---

## Architect #4 — Control Flow & Rest Logic

**Verdict: Decision ladder matches design; key gaps in no-tool termination and force_rest_reason propagation**

### [High] `react_think` no-tool-after-retry path → `subagent_rest` WITHOUT check_stack

- Evidence: `sagas/react_think.py:119-136, 176-186, 228-232`.
- Impact: Agent can rest with open skill scopes if LLM returns empty tool_calls twice; violates "rest ⇔ stack empty" invariant.
- Fix: Gate `should_terminate` on Cortex `stack_depth == 0` (or explicit error), or merge check_stack into this decision.

### [Medium] Parallel `execute_tools` can race stack mutators

### [Medium] `chat_reply` has no per-session counter

### [Low] `force_rest_reason` not propagated into `subagent_rest`

### [Low] No explicit "Meta auto-closed" artifact in subagent_rest

### [Info] Cortex HTTP `skill_begin` does not enforce `max_skill_depth`

---

## Architect #5 — API Contract & Schema

**Verdict: Mostly consistent; asymmetric Runtime handling of skill_begin vs skill_end needs alignment**

### [High] `handle_cortex_skill_begin` raises vs `handle_cortex_skill_end` returns success

- Evidence: `cortex_handlers.py:79-84` raises on `ok: false`; `109-114` returns `success: True`.
- Fix: Align semantics — both raise on `ok: false` or both return `success: false`.

### [Medium] `cortex_bridge` uses `warning` field on HTTP failure, not `error`

### [Medium] Two "stack" implementations in Cortex may drift (`_collect_active_stack` vs `ContextEngine.status`)

### [Medium] Docs (`internal-api-schemas.md`) under-spec error response `stack`/`stack_depth`

### [Low] Pydantic models not strict / extras ignored

### [Low] `/v1/scope/create` and `/v1/scope/end` have no idempotency key in contract

### [Low] `RuntimeError` from skill_begin is generic → retries (should be `BusinessError`)

---

## Architect #6 — Observability & Operations

**Verdict: Correlatable via scope_id; but log_cortex may be no-op, rest decision not logged on happy path, no first-class trace_id, health endpoints static**

### [P1] `log_cortex` may be no-op if `novaic_cortex.observability` missing

- Evidence: `workspace.py:29-34` try/except fallback.
- Fix: Ship `observability.py` or remove try/except; document required module.

### [P1] "Why rest?" is unclear on happy path

- Evidence: `sagas/react_actions.py:103-210` — only logs when `round_cap` or `stack_known=False`; normal `stack_depth==0` rest has no structured log.
- Fix: One structured log line at `_decide_rest_or_continue` with `stack_empty, stack_depth, stack_known, round_num, force_rest_reason, scope_id`.

### [P2] Skill push/pop on hot path — no INFO success logs

### [P2] Cortex `context_skill_begin/end` don't call `log_cortex`

### [P2] Every task completion logs INFO — noisy under load

### [P2] Saga failure log: error text only, no step_name/topic

### [P3] `/health` static — no store/OSS/lock probe

### [P3] ~~Missing worker modules~~ — FALSE POSITIVE (see §0)

### [P3] No Prometheus-style counters for `skills_*, archives, auto_closes, lock_waits`

### [P4] Several handlers `logger.error` then return `success: True with error`

---

## Architect #7 — Performance & Scalability

**Verdict: Hot paths mostly depth-bounded; skill_begin pays full tree walk; _SKILL_LOCKS can leak on abandoned sessions**

### [High] `_SKILL_LOCKS` leak on abandoned roots

- Evidence: `cortex/api.py` — `_drop_scope_lock` only on successful `is_root` scope_end.
- Fix: TTL/LRU eviction; periodic sweep; weakref.

### [Medium] `skill_begin` does O(nodes) tree walk per call

- Evidence: `api.py:443-447, 459-465` `_walk_scope_tree` for global `child_scope_id` uniqueness.
- Fix: Bloom/hash-set index in root meta.

### [Medium] `create_scope` lists `steps/` for seq allocation (extra full listing)

### [Low] `resolve_active_scope_path` is O(depth) up to 20 levels

### [Low] Parallel-step polling at 100ms

### [Info] `_budget_compact` runs every `prepare_for_llm` (debounced)

### [Info] Cortex single-process

### [Unknown] `move_prefix` atomicity

---

## Architect #8 — Security & Multi-Tenancy

**Verdict: Data isolation relies on storage key prefixing; internal APIs are "trusted network", no crypto auth**

### [High] Cortex internal `/v1/`* are caller-supplied tenant fields with no auth

- Evidence: `cortex/api.py:217-221, 342-360, 739-745` — `_TenantMixin` accepts user_id/agent_id from body; docstring says "no auth".
- Fix: mTLS or shared secret between services.

### [High] Queue Service has no auth on publish/claim/sagas/dispatch

- Fix: Loopback-bind + HMAC / mTLS.

### [Medium] Gateway `auth.py:402-459` documented as Clerk JWKS + HS256, but only calls HS256 path

### [Medium] `TRUST_GATEWAY_X_USER_ID` defaults true

### [Medium] `get_cortex_bridge` cache key is `scope_id` only

### [Low] `business/internal/subagent.py:64-84` `get_subagents_due_for_wake` doesn't include `user_id` — scheduler then drops wake

---

## Synthesis — What the design gets right

- **Cortex = single source of truth**（scope 树、skill LIFO 栈、steps 时间线、归档）。
- **4 级 rest 决策**：round cap → unknown → empty → continue，配合 fail-safe，栈状态不明不入睡。
- **Wake 路径强约束**：`auto_meta_skill` 非 optional、`user_id` 强制，scheduler 也兜底丢弃无 user_id 的 wake。
- **归档前自动收尾**：`_auto_close_open_children` DFS 关子 scope 防泄漏。
- **并发骨架**：per-root `asyncio.Lock`（`_SKILL_LOCKS`） + 全局 `child_scope_id` 唯一 + LIFO 强校验。
- **Saga 补偿闭环**：wake/think/actions 任一失败都会触发 `subagent_rest` 补偿。
- **Queue 幂等骨架**：DAG step key 稳定（`{saga_id}-{step_name}`）+ publish 去重 + task ledger。
- **租户隔离**：存储 key 前缀化、`_TenantMixin` 强制 user_id+agent_id、`/dispatch` 拒空。
