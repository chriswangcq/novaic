# Runtime saga prepare-context ordering map result

## Summary

Aggregated the closed split children for the ReAct saga prepare-context ordering map. The active source path shows `prepare_context -> call_llm -> save_response`, and a focused DAG guard now pins `call_llm.depends_on == ["prepare_context"]`.

## Done

- `P164/R143/C157` mapped the source-level order:
  - `prepare_context` is declared immediately before `call_llm`.
  - `SagaDefinition.to_dag()` gives linear steps `depends_on=[previous_step]`.
  - task execution passes the dependency result into two-argument payload builders.
  - `build_llm_call_payload` copies `messages` and `tools` from the prepare result.
- `P165/R144/C158` added a focused regression guard:
  - `prepare_context` appears before `call_llm`.
  - `call_llm.depends_on == ["prepare_context"]`.
  - `save_response.depends_on == ["call_llm"]`.

## Verification

- Source mapping test run: `17 passed`.
- Guard patch test run: `17 passed`.
- Focused command: `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/integration/test_saga_dag_refactor.py novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`.

## Known Gaps

- This parent only proves saga ordering and dependency handoff. Handler response shape, final LLM payload shape, continuity residue, and broader regression coverage remain sibling problems under `P135`.

## Artifacts

- `novaic-agent-runtime/task_queue/sagas/react_think.py`
- `novaic-agent-runtime/task_queue/contracts/react_think.py`
- `novaic-agent-runtime/task_queue/saga.py`
- `novaic-agent-runtime/task_queue/workers/task_execution.py`
- `novaic-agent-runtime/tests/integration/test_saga_dag_refactor.py`
- `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`
