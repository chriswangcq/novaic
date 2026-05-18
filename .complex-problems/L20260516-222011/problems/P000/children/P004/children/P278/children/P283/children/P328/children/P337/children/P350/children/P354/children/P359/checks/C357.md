# P359 success check

## Summary

Success. R336 closes the gating-order problem: terminal subagent status tasks no longer run before the session-generation-owned finalize transition, and a rejected finalize no longer satisfies saga dependencies.

## Evidence

- `novaic-agent-runtime/task_queue/sagas/wake_finalize.py:4` documents the flow as Cortex archive -> Session Coordinator -> gated terminal subagent status.
- `novaic-agent-runtime/task_queue/sagas/wake_finalize.py:121` registers `session_ended` before terminal status tasks.
- `novaic-agent-runtime/task_queue/sagas/wake_finalize.py:132` and `:140` explicitly set both terminal status tasks to depend on `session_ended`.
- `novaic-agent-runtime/task_queue/saga.py:82`, `:123`, and `:209` add explicit task-step `depends_on` support through `SagaDefinition.to_dag()`.
- `novaic-agent-runtime/task_queue/handlers/session_handlers.py:80` raises `BusinessError` when the session coordinator returns `finalize_rejected`, so stale finalize rejection does not become a successful dependency result.
- `novaic-agent-runtime/tests/test_runtime_tool_path_contract.py:66` asserts the wake-finalize step order and `:75` asserts both terminal status tasks depend on `session_ended`.
- `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py:344` asserts rejected finalize action fails the task gate.
- Manual DAG spec print from R336 confirmed `set_subagent_sleeping` and `set_subagent_completed` both depend on `session_ended`.

## Criteria Map

- Inspect DAG definition and executor dependency behavior: met. `to_dag()` emits `depends_on`, `dag_builder` propagates it, task source releases dependency-unmet tasks, and BusinessError prevents successful step result publication.
- Reorder/gate terminal status tasks after `session_ended`: met by wake-finalize order and explicit dependencies.
- Add tests proving generated DAG order and status dependencies: met by `test_runtime_tool_path_contract.py`.
- If executor semantics do not preserve intended gate, split/fix rather than relying on hope: met by fixing the discovered reject-as-success hole in `session_handlers.py`.
- Preserve Cortex scope_end ordering intentionally: met; it remains first and `session_ended` depends on it.

## Execution Map

- Code changed:
  - `novaic-agent-runtime/task_queue/saga.py`
  - `novaic-agent-runtime/task_queue/sagas/wake_finalize.py`
  - `novaic-agent-runtime/task_queue/handlers/session_handlers.py`
- Tests changed:
  - `novaic-agent-runtime/tests/test_runtime_tool_path_contract.py`
  - `novaic-agent-runtime/tests/integration/test_saga_dag_refactor.py`
  - `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py`
- Commands run:
  - `python3 -m py_compile task_queue/sagas/wake_finalize.py task_queue/saga.py task_queue/dag_builder.py task_queue/workers/task_sources.py task_queue/handlers/session_handlers.py`
  - `PYTHONPATH=.:../novaic-common pytest -q tests/test_runtime_tool_path_contract.py tests/test_pr254_finalize_ownership.py tests/test_pr311_saga_compensation_outbox_cutover.py tests/integration/test_saga_dag_refactor.py`
  - `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr43_last_scope_wiring.py tests/test_runtime_tool_path_contract.py tests/test_pr254_finalize_ownership.py tests/test_pr311_saga_compensation_outbox_cutover.py tests/integration/test_saga_dag_refactor.py`

## Stress Test

- Plausible failure mode: `session_ended` returns `{"action": "finalize_rejected"}` for a stale generation but the task is still treated as completed, unblocking terminal status tasks. This was discovered during execution and fixed by raising `BusinessError`; the new test asserts that rejected finalize fails the task gate.

## Residual Risk

- Aggregate residue scanning remains P360. No P359-blocking risk remains: status tasks are directly dependent on `session_ended`, and rejected finalize no longer creates a successful dependency result.

## Result IDs

- R336
