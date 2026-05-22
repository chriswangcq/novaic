# P006: Migrate LLM Factory Data to Postgres With Row-Count Validation

Status: done
Parent: P003
Root: P000
Source Ticket: T003 (split)
Source Check: none
Package: problems/P000/children/P003/children/P006
Body: problems/P000/children/P003/children/P006/README.md
Ticket(s): T005

## Problem
The existing `/opt/novaic/llm-factory/data/llm_factory.db` contains production API keys, model definitions, user keys, and logs. This data must be copied into the dedicated `novaic_llm_factory` Postgres database without losing rows or changing sensitive logging configuration.

This belongs under the LLM Factory migration split because data migration has its own backup, transformation, and verification requirements separate from code support and runtime cutover.

## Success Criteria
- The SQLite database is backed up before migration.
- Pre-migration row counts are recorded for `api_keys`, `models`, `user_keys`, and `llm_logs`.
- Data is imported into Postgres using an idempotent or safely repeatable process.
- Post-migration Postgres row counts match the recorded SQLite counts.
- Sensitive request/response body log fields remain empty/disabled according to current policy.

## Subproblems
- none

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/children/P003/children/P006/README.md
- Ticket T005: problems/P000/children/P003/children/P006/tickets/T005.md
- Result R003: problems/P000/children/P003/children/P006/results/R003.md
- Check C003: problems/P000/children/P003/children/P006/checks/C003.md

## Follow-ups
- none
