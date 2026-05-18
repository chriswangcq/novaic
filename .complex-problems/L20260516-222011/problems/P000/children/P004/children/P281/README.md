# Queue FSM focused verification

## Problem

Run focused queue/session/FSM/outbox/finalize tests and final residue scans after any cleanup from sibling problems.

## Success Criteria

- Focused queue-service tests pass.
- Static residue scan has no unclassified risky legacy path.
- Exact commands and counts are recorded.
