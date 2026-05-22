# P033: Implement Cortex Postgres Operational Store

Status: done
Parent: P026
Root: P000
Source Ticket: T030 (split)
Source Check: none
Package: problems/P000/children/P024/children/P026/children/P033
Body: problems/P000/children/P024/children/P026/children/P033/README.md
Ticket(s): T031

## Problem
Cortex needs a Postgres-backed production operational store before production can switch away from `/opt/novaic/data/cortex/operational.sqlite3`.

## Success Criteria
- Cortex source supports a Postgres operational store for all five active operational tables.
- Postgres schema preserves primary keys, unique idempotency, indexes, and JSON/text behavior.
- Existing operational store API behavior is preserved.
- Focused Cortex tests pass locally.
- No production data, config, or runtime state is changed by this implementation-only problem.

## Subproblems
- none

## Results
- R029

## Latest Check
C029

## Bodies
- Problem: problems/P000/children/P024/children/P026/children/P033/README.md
- Ticket T031: problems/P000/children/P024/children/P026/children/P033/tickets/T031.md
- Result R029: problems/P000/children/P024/children/P026/children/P033/results/R029.md
- Check C029: problems/P000/children/P024/children/P026/children/P033/checks/C029.md

## Follow-ups
- none
