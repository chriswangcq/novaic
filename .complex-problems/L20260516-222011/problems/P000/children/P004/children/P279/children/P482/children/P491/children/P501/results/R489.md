# Recovery/session-ended contract inventory result

## Summary

Completed the read-only recovery/session-ended inventory. Session-ended/finalize contracts are strict, but suspected-dead recovery still drops stack diagnostics before archive shaping, allowing missing metadata to become a silent known-empty stack. That gap is routed to P502.

## Done

- Saved raw recovery/session guard output.
- Saved production-focused hits and file list.
- Wrote classification artifact with strict paths, cleanup candidates, existing tests, and conclusion.
- Made no source changes.

## Verification

- Raw guard artifact has `457` lines.
- Production-focused artifact has `87` lines.
- Classification artifact identifies exact P502 cleanup candidates in `saga_repo.py` and `session_recovery.py`.

## Known Gaps

- P502 must preserve explicit stack diagnostics in suspected-dead events and make unknown-stack recovery explicit.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p501/recovery-session-contract-raw-guards.txt`
- `.complex-problems/L20260516-222011/tmp/p501/recovery-session-production-hits.txt`
- `.complex-problems/L20260516-222011/tmp/p501/recovery-session-contract-files.txt`
- `.complex-problems/L20260516-222011/tmp/p501/recovery-session-contract-classification.md`
