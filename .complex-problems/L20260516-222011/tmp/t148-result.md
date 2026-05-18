# ReAct saga source ordering map result

## Summary

Mapped the active ReAct think saga ordering and dependency handoff. Source order is linear: `prepare_context` is declared immediately before `call_llm`, `SagaDefinition.to_dag()` makes each linear step depend on the previous step, and task execution passes the first dependency's step result as `prev_result` into two-argument payload builders. Therefore `call_llm` receives the `prepare_context` result through `_build_llm_call_payload`.

## Done

- Mapped `novaic-agent-runtime/task_queue/sagas/react_think.py:44-53`: `_build_prepare_context_payload(ctx)` builds the Cortex prepare payload; `_build_llm_call_payload(ctx, prev_result)` passes `prev_result` to `build_llm_call_payload(...)`.
- Mapped `novaic-agent-runtime/task_queue/sagas/react_think.py:146-158`: `prepare_context` is the first task step and `call_llm` is the immediately following task step.
- Mapped `novaic-agent-runtime/task_queue/saga.py:190-255`: `to_dag()` assigns each normal linear step `depends_on=[prev_name]`, so `call_llm` depends on `prepare_context`.
- Mapped `novaic-agent-runtime/task_queue/workers/task_execution.py:217-235` and `:347-371`: task execution selects `prev_result = step_results[depends_on[0]]` and passes it into `build_payload(ctx_with_results, prev_result)` when the payload builder accepts two parameters.
- Mapped `novaic-agent-runtime/task_queue/contracts/react_think.py:98-114`: `build_llm_call_payload(...)` copies `messages` and `tools` only from the `prepare_context_result`.
- Existing tests identified and run:
  - `test_saga_dag_refactor.py` covers saga DAG dependencies.
  - `test_runtime_explicit_contracts.py` covers explicit payload builders and authority guardrails.

## Verification

- Ran `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/integration/test_saga_dag_refactor.py novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`.
- Result: `17 passed`.

## Known Gaps

- Existing DAG test currently checks `trigger_actions` dependency but does not directly assert `call_llm -> prepare_context`. This is not fixed in this source-map ticket because sibling `P165` owns adding or confirming the focused ordering guard.
- This result does not judge handler response shape, LLM handler input shape, or continuity residue; those are separate `P160-P163` child problems.

## Artifacts

- `novaic-agent-runtime/task_queue/sagas/react_think.py`
- `novaic-agent-runtime/task_queue/contracts/react_think.py`
- `novaic-agent-runtime/task_queue/saga.py`
- `novaic-agent-runtime/task_queue/workers/task_execution.py`
- `novaic-agent-runtime/tests/integration/test_saga_dag_refactor.py`
- `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`
