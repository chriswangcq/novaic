# Recovery stack diagnostics hardening result

## Summary

Hardened recovery stack diagnostics. Suspected-dead events now include explicit `remaining_stack`, missing diagnostics become `{"known": false, "depth": 0, "frames": []}`, malformed explicit recovery stack data is rejected, and legacy `stack_known_at_finalize` / `stack_depth_at_finalize` fallback usage is gone from guarded runtime/test scope.

## Done

- Updated `novaic-agent-runtime/queue_service/saga_repo.py` so suspected-dead events persist explicit-or-unknown `remaining_stack`.
- Updated `novaic-agent-runtime/queue_service/session_recovery.py` so recovery archive shaping preserves dict `remaining_stack`, rejects malformed explicit stack values, and uses explicit unknown stack only when missing.
- Removed recovery archive reliance on `stack_known_at_finalize` and `stack_depth_at_finalize`.
- Updated focused recovery tests to expect unknown-stack semantics for missing diagnostics and preservation for explicit diagnostics.

## Verification

- Focused recovery/finalize suite passed: `37 passed in 0.35s`.
- Guard output has an empty `legacy stack fallback fields in runtime/test scope` section.
- Guard output shows explicit `remaining_stack` handling in `saga_repo.py` and `session_recovery.py`.

## Known Gaps

- P503 still needs final recovery/session-ended verification across this branch.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p502/recovery-stack-diagnostics-hardening-tests.log`
- `.complex-problems/L20260516-222011/tmp/p502/recovery-stack-diagnostics-hardening-guards.txt`
- `.complex-problems/L20260516-222011/tmp/p502/recovery-stack-diagnostics-hardening-diff.txt`
