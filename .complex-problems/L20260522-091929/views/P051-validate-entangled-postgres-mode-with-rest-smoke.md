# P051: Validate Entangled Postgres Mode With REST Smokes

Status: done
Parent: P040
Root: P000
Source Ticket: T045 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P040/children/P051
Body: problems/P000/children/P024/children/P027/children/P040/children/P051/README.md
Ticket(s): T052

## Problem
The migrated/staging Postgres target must be exercised by an Entangled process running in Postgres mode, not only by offline SQL checks. This belongs under `P040` because production cutover needs proof that the runtime starts, registers schemas, serves REST reads/writes, and does not open the SQLite database file in Postgres mode.

## Success Criteria
- A staging or local test Entangled process starts with `--db-backend postgres` against a safe test target.
- Health/readiness endpoints return success in Postgres mode.
- Process arguments and file-handle checks show Entangled is not opening the active SQLite database file.
- Schema registration completes without Postgres DDL errors.
- REST smoke checks pass for representative list/read, singleton upsert/read, stream append/query, update, delete, and CAS or equivalent rowcount-sensitive behavior.
- Smoke-test output is captured in a redacted report without secrets.
- Any unavailable auth/client dependency is explicitly documented with the smallest equivalent direct API proof and a follow-up gap if the REST behavior cannot be proven.

## Subproblems
- P057: Prepare Safe Entangled Postgres REST Staging Target
- P058: Start Entangled In Postgres Mode For REST Staging
- P059: Run Entangled Postgres REST Smoke Suite And Report

## Results
- R052

## Latest Check
C054

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P040/children/P051/README.md
- Ticket T052: problems/P000/children/P024/children/P027/children/P040/children/P051/tickets/T052.md
- Result R052: problems/P000/children/P024/children/P027/children/P040/children/P051/results/R052.md
- Check C054: problems/P000/children/P024/children/P027/children/P040/children/P051/checks/C054.md

## Follow-ups
- none
