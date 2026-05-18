# Runtime LLM prepare caller authority audit result

## Summary

Audited the runtime LLM prepare caller chain and found the active provider-message path is `react_think.prepare_context -> cortex.prepare_llm_context -> bridge.prepare_for_llm -> build_llm_call_payload -> llm.call`. `context.read` remains in the prepare handler only as a notification-hint merge step before Cortex read-model preparation; it is not the authority for final LLM `messages`.

## Done

- Mapped the saga path:
  - `novaic-agent-runtime/task_queue/sagas/react_think.py:149` registers `prepare_context` on `TaskTopics.CORTEX_PREPARE_LLM_CONTEXT`.
  - `novaic-agent-runtime/task_queue/sagas/react_think.py:155` registers `call_llm` on `TaskTopics.LLM_CALL`.
  - `novaic-agent-runtime/task_queue/sagas/react_think.py:52` builds the LLM call payload from the previous `prepare_context` step result.
- Mapped the prepare handler:
  - `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py:301` calls `context.read` only to merge current Environment notification hints.
  - `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py:325` calls `bridge.prepare_for_llm(agent_root_scope_id)` for the prepared Cortex snapshot.
  - `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py:347` passes `CortexPreparedContext` into `assemble_llm_request_from_snapshot`.
- Mapped the LLM call handler:
  - `novaic-agent-runtime/task_queue/contracts/react_think.py:98` copies `messages/tools` only from `prepare_context_result`.
  - `novaic-agent-runtime/task_queue/handlers/llm_handlers.py:120` delegates provider request shaping to `prepare_llm_call`.
  - `novaic-agent-runtime/task_queue/handlers/llm_handlers.py:136` sends `prepared.messages` to `LLMBusiness.call`.
- Removed stale wording in `novaic-agent-runtime/task_queue/sagas/react_think.py` that said LLM context assembly reads `context.jsonl`.
- Added `test_prepare_llm_context_uses_prepare_snapshot_not_context_read_projection` to prove `context.read` returned messages cannot enter the final LLM request if they differ from the `prepare_for_llm` snapshot.
- Added `test_llm_call_handler_does_not_read_cortex_context_as_authority` to guard the final LLM call handler from reintroducing `read_context` or `context.read` as authority.

## Verification

- `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py novaic-agent-runtime/tests/test_runtime_explicit_contracts.py` passed: `20 passed`.
- `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/test_no_tool_warning.py novaic-agent-runtime/tests/test_pr67_wake_child_scope.py` passed: `10 passed`.
- Residue search found runtime `read_context` only in `context_handlers.py`, `CortexBridge.read_context`, topic definitions, and tests for notification/context-read behavior; no direct `llm_handlers` authority path remains.

## Known Gaps

- `context.read` is still an active runtime topic for environment notification hint insertion and idempotency scanning. That is outside this ticket's authority boundary, but it remains a naming/architecture smell because the name sounds like LLM context authority.
- Existing tests in `test_no_tool_warning.py` still initialize `bridge.read_context.return_value` in helper setup. This is harmless for the current authority path but may deserve future cleanup if we want the tests to stop implying `read_context` is part of provider-message assembly.

## Artifacts

- Code/doc guard edits:
  - `novaic-agent-runtime/task_queue/sagas/react_think.py`
  - `novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py`
  - `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`
- Search evidence:
  - `rg -n "read_context\\(|context/read|context\\.read|read context\\.jsonl|read_context\\.return_value" novaic-agent-runtime/task_queue novaic-agent-runtime/tests -g '*.py'`
