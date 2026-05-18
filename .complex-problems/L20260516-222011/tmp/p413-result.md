# Finalize saga and session handler classification result

## Summary

Completed the P413 finalize saga/session handler classification. No dangerous session-generation fallback was found. `wake_finalize`, `subagent_wake`, and `session_handlers` use explicit positive generation validation for session identity, while finalize reason and remaining stack are required at the session handler boundary.

## Done

- Ran a targeted guard over `wake_finalize.py`, `subagent_wake.py`, and `session_handlers.py`.
- Classified `subagent_wake.py`:
  - `session_generation` is assigned through `require_positive_session_generation(ctx, "subagent_wake")`;
  - other `ctx.get(...)` uses are non-session identity metadata (`user_id`, `trigger_type`, `tools`, `model`, message IDs).
- Classified `wake_finalize.py`:
  - `_session_generation(ctx)` uses `require_positive_session_generation(ctx, "wake_finalize")`;
  - `round_num` and `stack_depth_at_finalize` use non-negative integer parsing as archive/loop metadata;
  - `finalize_reason` defaults to `stack_empty` only as archive reason metadata, not generation authority;
  - `remaining_stack` is snapshotted from explicit context or constructed as stack metadata, not active-session lookup.
- Classified `session_handlers.py`:
  - missing generation is rejected;
  - bool/non-positive/malformed generation is rejected;
  - `finalize_reason` and `remaining_stack` are required before calling `saga_client.session_ended(...)`.

## Verification

- Guard artifact: `.complex-problems/L20260516-222011/tmp/p413/finalize-session-handler-guard.txt`.
- Focused test run from `novaic-agent-runtime`:
  - `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr254_finalize_ownership.py tests/test_runtime_explicit_contracts.py tests/test_session_init_message_ids.py tests/test_pr43_previous_scope_transport.py tests/test_pr65_agent_root_scope.py tests/test_pr67_wake_child_scope.py`
  - Result: `48 passed in 0.38s`.

## Known Gaps

- None for P413's finalize saga/session handler scope.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p413/finalize-session-handler-guard.txt`
