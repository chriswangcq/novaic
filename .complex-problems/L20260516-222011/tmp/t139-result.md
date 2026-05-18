# context.jsonl caller classification result

## Summary

Classified all active `context.jsonl` helper callers and removed one unsafe compatibility behavior: runtime `CortexBridge.read_context` no longer soft-fails to `[]`, so projection corruption/transport failure cannot masquerade as empty history.

## Done

- Cortex API callers:
  - `api.py:840-850` `context_read`: public/debug projection read API.
  - `api.py:853-873` `context_append`: appends ContextEvent plus materialized projection.
  - `api.py:876-896` `context_batch`: appends ContextEvents plus materialized batch projection.
- Runtime callers:
  - `context_handlers.py:103-105`: reads projection for idempotency/dedupe of Environment notification projection messages.
  - `context_handlers.py:151-156`: appends missing notification projection messages.
  - `context_handlers.py:219`: appends regular context projection messages.
  - `runtime_handlers.py:143-149`: writes initial wake prompt/context projection batch.
  - `cortex_bridge.py:143-181`: transport wrappers for read/append/batch.
- Changed `CortexBridge.read_context` to fail closed instead of returning `[]` on any exception.
- Added `test_cortex_bridge_read_context_fails_closed`.

## Verification

- Ran `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/test_runtime_explicit_contracts.py novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py novaic-agent-runtime/tests/test_context_read_by_ids.py`.
- Result: `31 passed in 0.15s`.

## Known Gaps

- This result classifies callers; it does not prove the active LLM prepare path avoids `context.jsonl`. That remains under `P154`.

## Artifacts

- Modified `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`.
- Modified `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`.
