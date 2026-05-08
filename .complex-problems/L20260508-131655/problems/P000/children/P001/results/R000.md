# P001 Result - 审计 FSM substrate 与状态机接入

## Scope

审计范围覆盖 `novaic-agent-runtime/queue_service` 内的 generic FSM substrate、Session harness、Task lifecycle、Saga lifecycle 以及 wake creation durable outbox cutover。

## Evidence Read

- `novaic-agent-runtime/queue_service/fsm/core.py`
  - 提供 IO-free generic FSM primitive：`FsmStateSnapshot`、`FsmEvent`、`FsmEffect`、`FsmDecision`、`decide_transition`。
  - 设计明确要求 transition function 由调用方注入，primitive 本身不读取 clock/db/env/network。
- `novaic-agent-runtime/queue_service/fsm/sqlite_store.py`
  - 提供通用 SQLite event/state/outbox store。
  - 表名、字段名、machine id column、consumed/status columns 通过 `FsmSqliteStoreConfig` 显式传入。
- `novaic-agent-runtime/queue_service/session_fsm.py`
  - Session dispatch/finalize/recovery decision 已是 pure FSM decision。
  - 状态包括 `no_active | starting | active | ending | suspected_dead | recovering`。
- `novaic-agent-runtime/queue_service/session_ledger.py`
  - `tq_session_events`、`tq_session_state`、`tq_session_outbox` 由 generic store 承载。
  - event id/outbox id/clock 由构造参数注入。
- `novaic-agent-runtime/queue_service/session_repo.py`
  - dispatch 先 append input event，再基于 `session_state` 和 pure decision 决策。
  - start wake 只持久化 `CREATE_WAKE_SAGA` outbox intent，不在 dispatch 主路径直接创建 saga。
  - `list_active_sessions()` 已从 `session_ledger.list_active_states()` 读取。
- `novaic-agent-runtime/queue_service/session_outbox.py`
  - wake saga creation direct `saga_orchestrator.create()` 只存在于 durable outbox dispatcher side-effect adapter。
  - `PUBLISH_ATTACH_INPUT` 要求 `expected_session_generation`，避免旧 generation attach。
- `novaic-agent-runtime/queue_service/task_fsm.py` / `task_ledger.py`
  - Task lifecycle decision 已 pure FSM；ledger 使用 generic store 的 `tq_task_events/state/outbox`。
  - `TaskQueue.claim()` 使用 `tq_task_state` 作为候选权威，而不是旧 projection status。
- `novaic-agent-runtime/queue_service/saga_fsm.py` / `saga_ledger.py`
  - Saga lifecycle decision 已 pure FSM；ledger 使用 generic store 的 `tq_saga_events/state/outbox`。
  - `SagaOrchestrator.claim()` 使用 `tq_saga_state` 作为候选权威。
- `novaic-agent-runtime/queue_service/db/schema.py`
  - schema 注释明确：`tq_session_state` 是 session coordinator source of truth。
  - `tq_session_outbox` 是 durable side-effect ledger。

## Search Findings

`tq_active_sessions` 搜索结果：

- 运行时代码没有活表 SQL 引用。
- 剩余命中是：
  - `session_rebuild.py` 的函数名 `rebuild_active_sessions_from_sagas`
  - `routes.py` 的诊断接口 `list_active_sessions()`
  - 测试守卫确认 old table 不存在、不被引用。

Wake saga creation 搜索结果：

- `session_repo.dispatch()` 不直接 `SagaOrchestrator.create()`。
- direct `saga_orchestrator.create()` 只在 `SessionOutboxDispatcher._publish_create_wake_saga()`，即 durable outbox adapter。

## Verification

在 `novaic-agent-runtime` 执行：

```bash
pytest -q \
  tests/test_pr251_wake_creation_outbox_cutover.py \
  tests/test_pr252_session_state_ssot.py \
  tests/test_pr253_dispatch_pure_fsm_cutover.py \
  tests/test_pr257_remove_active_sessions_table.py \
  tests/test_pr258_generic_fsm_substrate.py \
  tests/test_pr259_generic_fsm_store_outbox.py \
  tests/test_pr260_session_harness_generic_fsm_cutover.py \
  tests/test_pr261_generic_fsm_residue_cleanup.py \
  tests/test_pr304_task_lifecycle_fsm.py \
  tests/test_pr306_taskqueue_fsm_cutover.py \
  tests/test_pr308_saga_lifecycle_fsm.py \
  tests/test_pr310_saga_repository_fsm_cutover.py \
  tests/test_pr315_queue_fsm_final_residue_guard.py
```

结果：`57 passed in 0.38s`。

## Conclusion

FSM substrate 已经存在并且是活路径。Session/Task/Saga 三条主生命周期都已接入 generic FSM store + pure decision + ledger/outbox。Session active pointer 已由 `tq_session_state` 接管，wake saga creation 已从 dispatch 主路径切到 durable session outbox。

## Remaining Gaps

- 还不是完全统一的 generic FSM runner。当前 substrate 提供 primitive/store，Session/Task/Saga repo 仍分别手写 `_record_*_transition`、projection apply、claim candidate SQL 等 adapter 流程。
- 还不是“业务只剩 DSL”。`SessionRepository`、`TaskQueue`、`SagaOrchestrator` 仍是较厚 coordinator/repository，虽然关键 decision 已 pure。
- 仍有 legacy vocabulary 残留，例如 `rebuild_active_sessions_from_sagas` 和 `list_active_sessions()` 名称，但这些不是旧表活路径。
