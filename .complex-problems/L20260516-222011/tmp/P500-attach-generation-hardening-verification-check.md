# Attach generation hardening verification check

## Summary

Success for P500. The verification result maps directly to each criterion: the focused suite passed, the forbidden optional generation contract guard is empty, attach-race tests were included, and attach publication references show generation-aware builder and outbox paths.

## Evidence

- R485 records the verification run and artifacts.
- `.complex-problems/L20260516-222011/tmp/p500/attach-generation-hardening-verification-tests.log` shows `33 passed`.
- `.complex-problems/L20260516-222011/tmp/p500/attach-generation-hardening-verification-guards.txt` has an empty forbidden optional generation contract section.
- `.complex-problems/L20260516-222011/tmp/p500/attach-generation-hardening-verification-diff.txt` records the implementation diff under verification.

## Criteria Map

- Focused attach/session tests pass after hardening: satisfied by the 33-test focused suite.
- `rg` guard checks show the optional attach builder generation contract is gone: satisfied by no hits for `expected_session_generation: int | None` or `expected_session_generation=None`.
- Existing attach-race buffering tests still pass: satisfied because `tests/test_pr248_attach_outbox_cutover.py` is included in the passing suite.
- No active no-generation `SESSION_ATTACH_INPUT` path remains: satisfied by guards showing `session_repo.py` uses `build_attach_input_effect()` with `expected_session_generation=session_generation`, `session_effects.py` validates with the canonical helper, and `session_outbox.py` validates before publishing.

## Execution Map

- T491 was a verification-only one-go ticket.
- R485 saved tests, guard output, and diff evidence.
- No implementation work was performed inside P500.

## Stress Test

- Plausible failure mode: attach-race buffering silently regresses while builder validation passes.
- The passing suite includes `test_pr248_attach_outbox_cutover.py`, which covers attach outbox and attach-race buffering behavior.

## Residual Risk

- This is a focused verification pass, not a full runtime e2e deployment smoke. That is acceptable for P500 because its scope is attach generation hardening.

## Result IDs

- R485
