# Wake finalize status gating order

## Problem Definition

`wake_finalize` currently publishes terminal subagent status tasks before `session_ended`. Since `session_ended` is the session-generation-owned transition, a stale finalize DAG can still mutate Business subagent status before the session coordinator rejects the generation.

The DAG builder appears to encode linear dependencies through `depends_on`, and task claiming releases tasks until dependencies exist in saga `step_results`. P359 must verify this execution semantics and then put `session_ended` before terminal Business status mutation.

## Proposed Solution

1. Inspect `SagaDefinition.to_dag()`, `dag_builder.build()`, and task dependency claiming to confirm linear step order gates downstream execution through `depends_on`.
2. Reorder `wake_finalize` so:
   - `cortex_scope_end` remains first, preserving current structural archive ordering.
   - `session_ended` runs after Cortex archive and before terminal subagent status mutation.
   - `set_subagent_sleeping` / `set_subagent_completed` depend on `session_ended`.
3. Update comments/docstring in `wake_finalize.py` so the ordering describes the generation gate explicitly.
4. Add or update tests proving the generated DAG/task specs place `session_ended` before both terminal status tasks and that their `depends_on` references `session_ended`.
5. If dependency semantics are not actually enforced, stop and spawn a blocking executor-semantics child problem instead of relying on order.

## Acceptance Criteria

- Source inspection documents the dependency path from saga step order to task release gating.
- Wake-finalize order is `cortex_scope_end` -> `session_ended` -> conditional terminal subagent status tasks.
- Tests assert `set_subagent_sleeping` and `set_subagent_completed` depend on `session_ended`.
- Cortex scope_end ordering is preserved intentionally and documented.
- No compatibility path allows terminal status tasks to bypass `session_ended`.

## Verification Plan

- `python3 -m py_compile task_queue/sagas/wake_finalize.py task_queue/saga.py task_queue/dag_builder.py task_queue/workers/task_sources.py`
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_runtime_tool_path_contract.py tests/test_pr254_finalize_ownership.py tests/test_pr311_saga_compensation_outbox_cutover.py tests/integration/test_saga_dag_refactor.py`
- Source review of `task_queue/sagas/wake_finalize.py` and DAG task specs for status tasks depending on `session_ended`.

## Risks

- `optional=True` is present on some saga steps but is not carried into `DagNode`; this ticket should not pretend optional semantics are a safety gate. The intended safety gate is dependency ordering plus session-ended failure preventing a completed dependency result.
- If existing tests encode the old order, update them to the new generation-safe order rather than preserving compatibility.

## Assumptions

- P357/P358 already ensure terminal status tasks carry and validate positive identity.
- `session_ended` rejects stale generation at the session coordinator boundary.
