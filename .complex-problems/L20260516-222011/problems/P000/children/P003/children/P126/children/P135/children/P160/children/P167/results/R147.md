# CortexBridge prepare_for_llm endpoint contract verified

## Summary

Verified the runtime bridge contract for `CortexBridge.prepare_for_llm` and added a focused regression test that locks the method to the ContextEvent prepare endpoint. No active fallback from prepare to `read_context` was found in the bridge or LLM prepare handler path.

## Done

- Mapped `CortexBridge.read_context` as the separate materialized projection endpoint at `novaic-agent-runtime/task_queue/utils/cortex_bridge.py:143`.
- Mapped `CortexBridge.prepare_for_llm` as the prepare endpoint at `novaic-agent-runtime/task_queue/utils/cortex_bridge.py:474`.
- Confirmed `prepare_for_llm` posts to `/v1/context/prepare_for_llm` with `{user_id, agent_id, scope_id}` at `novaic-agent-runtime/task_queue/utils/cortex_bridge.py:482`.
- Added `test_cortex_bridge_prepare_for_llm_uses_prepare_endpoint` at `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py:304` to assert endpoint path, tenant payload, and passthrough return identity.
- Searched runtime bridge/handler/test paths for `prepare_for_llm`, `/v1/context/prepare_for_llm`, `/v1/context/read`, and `read_context(`; the active LLM prepare handler uses `bridge.prepare_for_llm(...)`, while `read_context` remains in separate context-read handlers/tests.

## Verification

- `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/test_runtime_explicit_contracts.py novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py novaic-agent-runtime/tests/test_pr67_wake_child_scope.py`
- Result: `26 passed in 0.16s`.

## Known Gaps

- None for this narrow bridge endpoint contract. Sibling problems still cover runtime payload handoff, continuity/context.read residue classification, and broader prepare-context regression audit.

## Artifacts

- Modified `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`.
- Evidence commands: `rg -n "prepare_for_llm\\(|/v1/context/prepare_for_llm|/v1/context/read|read_context\\(" novaic-agent-runtime/task_queue novaic-agent-runtime/tests/test_runtime_explicit_contracts.py novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py`.
