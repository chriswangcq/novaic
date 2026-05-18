# Runtime read_context caller inventory completed

## Summary

Inventoried runtime `read_context` / `context.read` production occurrences and guard coverage. The only active production caller of `CortexBridge.read_context` is `handle_context_read`; the only active production prepare-path use is `cortex_handlers.handle_cortex_prepare_llm_context` calling `handle_context_read` for notification hints, with provider messages still sourced from `bridge.prepare_for_llm`.

## Done

- Production inventory:
  - `context_handlers.py:81-104`: `context.read` topic handler reads Cortex context and appends notification hints; classified active-safe inspection/notification-hint side path.
  - `cortex_handlers.py:302-303`: prepare handler invokes `handle_context_read`; classified active-safe because `P166` and PR-85 guardrails prove `read_result.context` is not provider-message authority.
  - `cortex_bridge.py:143`: bridge method for materialized projection read; classified active-safe only through context-read handlers, fail-closed by earlier guard.
  - `runtime_handlers.py` continuity mentions are comments/contracts; active behavior writes explicit current inputs and generation-checked attach only, classified by `P174`.
  - Other production occurrences are comments, topic declarations, or retired-continuity notes.
- Test-only occurrences grouped as guard coverage, not active code: by-id/order tests, no-wake-replay tests, prepare snapshot authority tests, retired-history injection tests, and runtime explicit contract tests.

## Verification

- `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/test_context_read_by_ids.py novaic-agent-runtime/tests/test_context_read_ordering.py novaic-agent-runtime/tests/test_pr113_no_wake_im_replay.py novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py novaic-agent-runtime/tests/test_runtime_explicit_contracts.py novaic-agent-runtime/tests/test_pr57_prev_scope_history_inject.py novaic-agent-runtime/tests/test_pr43_previous_scope_transport.py novaic-agent-runtime/tests/test_pr186_runtime_main_path_acceptance.py`
- Result: `41 passed in 0.24s`.

## Known Gaps

- None for the runtime `read_context` caller inventory.

## Artifacts

- No code changes were required for this leaf.
