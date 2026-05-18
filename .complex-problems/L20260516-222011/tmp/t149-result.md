# ReAct saga prepare-context ordering guard result

## Summary

Added a focused regression guard for the active `react_think` DAG. The test now asserts `prepare_context` appears before `call_llm`, `call_llm.depends_on == ["prepare_context"]`, and `save_response.depends_on == ["call_llm"]`.

## Done

- Identified existing DAG test coverage as too broad: it only asserted `trigger_actions` depends on `decide_actions`.
- Updated `novaic-agent-runtime/tests/integration/test_saga_dag_refactor.py` to pin the `prepare_context -> call_llm -> save_response` dependency chain.
- Preserved the existing `trigger_actions -> decide_actions` assertion using a `by_name` lookup.

## Verification

- Ran `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/integration/test_saga_dag_refactor.py novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`.
- Result: `17 passed`.

## Known Gaps

- None for this guard leaf. Handler response shape and local continuity residue are separate sibling problems.

## Artifacts

- `novaic-agent-runtime/tests/integration/test_saga_dag_refactor.py`
