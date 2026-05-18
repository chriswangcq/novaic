# Attach builder strictness implementation result

## Summary

Hardened `build_attach_input_effect()` so attach effect construction validates an explicit positive session generation before returning a durable outbox effect. Added focused builder-boundary tests for invalid generations and valid normalization while preserving the existing attach payload shape.

## Done

- Updated `novaic-agent-runtime/queue_service/session_effects.py` to import and use `require_positive_session_generation_value()`.
- Changed `build_attach_input_effect()` from an optional generation contract to an explicit positive generation contract.
- Normalized the value written to `payload["expected_session_generation"]` through the canonical helper.
- Added focused tests in `novaic-agent-runtime/tests/test_pr267_session_outbox_effect_boundary.py` for `None`, bool, zero, non-integer text, and a valid value.

## Verification

- Ran focused attach/session suite: `28 passed in 0.12s`.
- Verified no remaining `expected_session_generation: int | None` or `expected_session_generation=None` hits in `novaic-agent-runtime/queue_service` or `novaic-agent-runtime/tests`.
- Reviewed the source diff for the two touched files.

## Known Gaps

- P500 still needs an independent final verification pass for P497, including attach-race buffering and guard evidence.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p499/attach-builder-strictness-tests.log`
- `.complex-problems/L20260516-222011/tmp/p499/attach-builder-strictness-guards.txt`
