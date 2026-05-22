# P003: Migrate llm-factory from SQLite to Postgres

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T003

## Problem
`llm-factory` is already Dockerized and has a small SQLite database, making it the safest first application migration to Postgres. The migration must preserve api keys, models, user keys, and logs while keeping request/response body logging disabled.

## Success Criteria
- `llm-factory` supports a Postgres DSN or adapter without permanent confusing dual paths.
- Existing SQLite data is migrated into `novaic_llm_factory` Postgres database with matching row counts.
- The service runs from Docker against Postgres and passes `/health` plus representative config/log queries.
- SQLite file is retained as rollback backup or archived with a clear non-current label.
- Rollback instructions are recorded.

## Subproblems
- P005: Add Explicit Postgres Backend Support to LLM Factory
- P006: Migrate LLM Factory Data to Postgres With Row-Count Validation
- P007: Cut Over LLM Factory Docker Runtime to Postgres and Label SQLite Rollback

## Results
- R005

## Latest Check
C005

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T003: problems/P000/children/P003/tickets/T003.md
- Result R005: problems/P000/children/P003/results/R005.md
- Check C005: problems/P000/children/P003/checks/C005.md

## Follow-ups
- none
