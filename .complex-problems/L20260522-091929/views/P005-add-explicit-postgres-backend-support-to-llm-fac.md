# P005: Add Explicit Postgres Backend Support to LLM Factory

Status: done
Parent: P003
Root: P000
Source Ticket: T003 (split)
Source Check: none
Package: problems/P000/children/P003/children/P005
Body: problems/P000/children/P003/children/P005/README.md
Ticket(s): T004

## Problem
`llm-factory` currently appears to use a SQLite-oriented database layer and config path. Before migrating production data, the service needs an explicit, tested Postgres backend path that can run against the `novaic_llm_factory` database without confusing dual-state.

This belongs under the LLM Factory migration split because data migration and Docker cutover cannot be safe until the application can intentionally talk to Postgres.

## Success Criteria
- The current `llm-factory` database/config implementation is inspected and documented.
- A Postgres-capable adapter/config path exists, or an existing one is confirmed with evidence.
- The Postgres schema for `api_keys`, `models`, `user_keys`, and `llm_logs` is created idempotently.
- SQLite remains available as a rollback backend until cutover is complete.
- Local or container-level smoke tests verify basic read/write operations against Postgres.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P003/children/P005/README.md
- Ticket T004: problems/P000/children/P003/children/P005/tickets/T004.md
- Result R002: problems/P000/children/P003/children/P005/results/R002.md
- Check C002: problems/P000/children/P003/children/P005/checks/C002.md

## Follow-ups
- none
