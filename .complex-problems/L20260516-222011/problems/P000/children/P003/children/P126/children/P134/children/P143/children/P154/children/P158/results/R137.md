# LLM prepare authority residue guard result

## Summary

Installed and verified regression guards for the LLM prepare authority boundary. The guards now cover both behavior and source shape: final LLM messages must come from Cortex `prepare_for_llm`, and the final `llm.call` handler must not call `read_context`/`context.read` directly.

## Done

- Confirmed existing guard coverage in `test_prepare_llm_context_rejects_missing_cortex_snapshot_fields`: missing Cortex prepared stack fails instead of falling back to `context.read`.
- Added behavioral guard `test_prepare_llm_context_uses_prepare_snapshot_not_context_read_projection`:
  - `bridge.read_context` returns `"legacy context.read projection"`.
  - `bridge.prepare_for_llm` returns `"prepared read-model snapshot"`.
  - The final `result["messages"]` includes only the prepared snapshot, not the legacy projection.
- Added static guard `test_prepare_llm_context_static_authority_contract`:
  - Requires `bridge.prepare_for_llm`.
  - Requires `CortexPreparedContext.from_mapping(prepare_result)`.
  - Requires `cortex_context=cortex_context` in assembly.
  - Forbids feeding `read_result.get("context")` / `read_result['context']` into assembly.
- Added final-handler guard `test_llm_call_handler_does_not_read_cortex_context_as_authority`:
  - Forbids `read_context` and `context.read` in `llm_handlers`.
  - Requires the runtime chain still includes `TaskTopics.CORTEX_PREPARE_LLM_CONTEXT` and `TaskTopics.LLM_CALL`.
- Cleaned the stale `react_think` flow comment from `read context.jsonl` to `ContextEvent read model`.

## Verification

- `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py novaic-agent-runtime/tests/test_runtime_explicit_contracts.py novaic-agent-runtime/tests/test_runtime_tool_path_contract.py` passed: `29 passed`.
- `rg -n "context\\.jsonl|read_context|context/read|context\\.read|prepare_for_llm|prepare_llm_context" novaic-agent-runtime/task_queue novaic-agent-runtime/tests -g '*.py'` was reviewed and classified:
  - allowed runtime code: `context_handlers.py`, `CortexBridge.read_context`, topic definitions.
  - LLM authority code: `cortex_handlers.py`, `react_think.py`, `llm_handlers.py`, with new guards.
  - tests: notification/context-read behavior tests plus new prepare authority guards.

## Known Gaps

- `context.read` remains a legitimate runtime topic name for notification-hint insertion. This ticket did not rename the topic because the success criteria only require guarding against LLM authority regression.
- Some comments/tests still mention `context.jsonl` for persistence/projection behavior outside the LLM prepare authority path. They are not blocking for this problem.

## Artifacts

- `novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py`
- `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`
- `novaic-agent-runtime/task_queue/sagas/react_think.py`
