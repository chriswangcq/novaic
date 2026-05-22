# P085: Port Task Mutations And State Locking To Postgres

Status: done
Parent: P080
Root: P000
Source Ticket: T077 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P085
Body: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P085/README.md
Ticket(s): T079

## Problem
Task publish, complete, fail, heartbeat, release, and cancel paths currently rely on process-local transaction locks and SQLite update behavior. The Postgres path needs explicit task-state row locking or compare-and-update semantics so single-task lifecycle mutations do not race with claim/recovery or duplicate workers. This belongs under P080 because these operations own the task lifecycle correctness after a candidate has been selected.

## Success Criteria
- Postgres task publish writes content/state/event/outbox rows with JSONB-compatible values and preserves idempotency-key behavior.
- Postgres task complete/fail/heartbeat/release/cancel lock or compare/update the relevant `tq_task_state` rows before applying lifecycle decisions.
- Task `_get_task_for_update` or its Postgres equivalent uses `FOR UPDATE` or a reviewed compare-and-update pattern.
- Postgres task mutation paths do not depend on `sqlite_busy_timeout_ms` or local process locks for correctness.
- Focused tests cover mutation loser/no-op behavior, completion versus recovery race shape, JSONB result binding, and existing sqlite mutation fixture compatibility.

## Subproblems
- none

## Results
- R075

## Latest Check
C080

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P085/README.md
- Ticket T079: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P085/tickets/T079.md
- Result R075: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P085/results/R075.md
- Check C080: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P085/checks/C080.md

## Follow-ups
- none
