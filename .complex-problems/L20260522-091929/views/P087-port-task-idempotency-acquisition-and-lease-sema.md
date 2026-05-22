# P087: Port Task Idempotency Acquisition And Lease Semantics To Postgres

Status: done
Parent: P086
Root: P000
Source Ticket: T080 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/children/P087
Body: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/children/P087/README.md
Ticket(s): T081

## Problem
`acquire_idempotency_execution` currently reads `tq_idempotency_ledger`, parses `lease_until` in Python, and then updates rows with SQLite-shaped assumptions. The Postgres path needs transaction-safe acquisition semantics for one `idempotency_key`: new row insert, completed-result reuse, active in-progress duplicate rejection, expired lease reacquire, contention counter updates, and same-owner renewal behavior. This belongs under T080 because acquisition is the first correctness boundary that prevents duplicate external side effects.

## Success Criteria
- Postgres acquisition locks or atomically updates the target `idempotency_key` row before deciding the returned action.
- Completed rows return `{"action": "completed", "result": ...}` with JSONB-native result handling and without JSON string double-decoding bugs.
- Active in-progress rows owned by another token return `{"action": "in_progress"}` and increment contention metadata.
- Expired in-progress rows can be reacquired using native timestamptz comparison in SQL, not Python ISO parsing.
- Same-owner acquisition behavior is explicitly covered and remains compatible with existing worker retry expectations.
- Focused tests cover missing key, new acquisition, active duplicate, expired reacquire, completed duplicate, contention update, and sqlite compatibility.

## Subproblems
- none

## Results
- R076

## Latest Check
C081

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/children/P087/README.md
- Ticket T081: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/children/P087/tickets/T081.md
- Result R076: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/children/P087/results/R076.md
- Check C081: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/children/P087/checks/C081.md

## Follow-ups
- none
