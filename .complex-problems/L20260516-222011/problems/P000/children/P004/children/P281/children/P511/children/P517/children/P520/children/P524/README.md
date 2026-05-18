# Rerun Full Session Outbox Finalize Focused Subset

## Problem

After fixing the three P517 failures, the full 52-file session/outbox/finalize focused subset must be rerun to prove the repairs close the parent failure.

## Success Criteria

- Rerun the full P517 subset using `.complex-problems/L20260516-222011/tmp/p517/session-outbox-finalize-test-files.txt`.
- Pytest exits successfully.
- Exact command, count, and log path are recorded.
