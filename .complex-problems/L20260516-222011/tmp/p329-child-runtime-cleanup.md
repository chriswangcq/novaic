# Runtime compatibility residue cleanup

## Problem

Runtime queue/session/task paths may still contain compatibility residue that accepts missing, stale, bool, malformed, or implicitly looked-up generation for attach/finalize/session-ended behavior. Any live runtime residue found by the inventory must be removed and covered with focused tests.

## Success Criteria

- Inspect all runtime queue/session/task hits from the inventory matrix.
- Remove dangerous runtime compatibility branches or replace them with explicit validators.
- Delete or rewrite tests that encode unsafe missing/stale generation success.
- Add focused regression tests for every changed live runtime boundary.
- Rerun runtime-focused tests and runtime guard searches until no unclassified runtime residue remains.
