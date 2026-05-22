# P084: Add Task Queue Postgres Claim Recovery And JSONB Query Dialect

Status: done
Parent: P080
Root: P000
Source Ticket: T077 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P084
Body: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P084/README.md
Ticket(s): T078

## Problem
Task candidate selection, stale recovery, dependency readiness, and cancel-by-agent currently use SQLite-specific SQL in `queue_service/queue_db.py`, including `datetime(...)`, `json_each`, and `json_extract`. Before task mutations can be fully ported, the Postgres path needs explicit query helpers for claim/recovery/cancel candidate SQL using JSONB and native timestamptz semantics. This belongs under P080 because these queries decide which tasks are visible and safe to mutate.

## Success Criteria
- Task claim candidate SQL for Postgres uses native timestamptz retry checks and `FOR UPDATE SKIP LOCKED` or an equivalent explicit compare-and-update candidate strategy.
- Task dependency readiness uses `jsonb_array_elements_text` and `COALESCE(step_results, '{}'::jsonb) ? dep.step_name` or an equivalent JSONB predicate.
- Task stale recovery uses native lease heartbeat timestamptz comparisons rather than SQLite `datetime(...)`.
- Task cancel-by-agent uses `payload ->> 'agent_id'` instead of `json_extract`.
- Focused tests assert the Postgres SQL/predicate forms and that sqlite query behavior remains available for existing fixtures.

## Subproblems
- none

## Results
- R074

## Latest Check
C079

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P084/README.md
- Ticket T078: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P084/tickets/T078.md
- Result R074: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P084/results/R074.md
- Check C079: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P084/checks/C079.md

## Follow-ups
- none
