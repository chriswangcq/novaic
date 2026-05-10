# P011: Strengthen ContextEvent stream identity validation

Status: done
Parent: P007
Root: P000
Package: problems/P000/children/P002/children/P007/children/P011
Body: problems/P000/children/P002/children/P007/children/P011/README.md
Ticket(s): T004

## Problem
The ContextEvent schema currently accepts delimiter-ambiguous stream identities. Since `stream_id` is defined as `user_id/agent_id/root_scope_id`, each segment must be non-empty and must not contain `/`, and persisted `stream_id` values must parse to exactly three segments. Without this, event ordering and idempotency can be ambiguous across roots or agents.

## Success Criteria
- `build_stream_id` rejects `/` in `user_id`, `agent_id`, and `root_scope_id`.
- `ContextEvent.validate` rejects stream ids that do not parse to exactly three non-empty segments.
- `ContextEvent.validate` requires the parsed root segment to equal `root_scope_id`.
- Tests cover valid stream id, slash-containing build inputs, missing segments, extra segments, and root mismatch.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P002/children/P007/children/P011/README.md
- Ticket T004: problems/P000/children/P002/children/P007/children/P011/tickets/T004.md
- Result R002: problems/P000/children/P002/children/P007/children/P011/results/R002.md
- Check C002: problems/P000/children/P002/children/P007/children/P011/checks/C002.md

## Follow-ups
- none
