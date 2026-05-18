# LLM payload handoff regression coverage audited

## Summary

Audited the regression coverage for the prepared-snapshot-to-provider handoff. Existing and newly tightened tests now cover the saga builder, bridge endpoint, Cortex prepare snapshot authority, handler delegation, pure LLM contract preprocessing, and saga DAG ordering.

## Done

- Identified `test_react_think_payload_builders_use_explicit_snapshot` at `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py:34`, now guarding stale local tools against entering `llm.call`.
- Identified `test_prepare_llm_call_has_injected_preprocessing_dependencies` at `test_runtime_explicit_contracts.py:100`, now guarding explicit payload tools and preprocessing order.
- Identified `test_llm_call_handler_does_not_read_cortex_context_as_authority` at `test_runtime_explicit_contracts.py:253`, guarding handler source against `read_context`/`context.read`.
- Identified `test_cortex_bridge_prepare_for_llm_uses_prepare_endpoint` at `test_runtime_explicit_contracts.py:308`, guarding bridge endpoint and payload.
- Identified `test_prepare_llm_context_uses_prepare_snapshot_not_context_read_projection` at `test_pr85_llm_context_smoke_guardrails.py:131`, guarding prepared snapshot authority over legacy `context.read` projection.
- Identified saga DAG ordering guard in `test_saga_dag_refactor.py`, which asserts `prepare_context` precedes `call_llm` and `call_llm` depends on `prepare_context`.

## Verification

- `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/test_runtime_explicit_contracts.py novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py novaic-agent-runtime/tests/test_pr67_wake_child_scope.py novaic-agent-runtime/tests/integration/test_saga_dag_refactor.py`
- Result: `31 passed in 0.35s`.

## Known Gaps

- None for regression coverage across this handoff chain.

## Artifacts

- `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`
- `novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py`
- `novaic-agent-runtime/tests/integration/test_saga_dag_refactor.py`
