# P104: Validate Queue Migration Timestamp Binding

Status: done
Parent: P075
Root: P000
Source Ticket: none (none)
Source Check: C107
Package: problems/P000/children/P024/children/P028/children/P075/children/P104
Body: problems/P000/children/P024/children/P028/children/P075/children/P104/README.md
Ticket(s): T102

## Problem
P075 migration tooling copies timestamp columns as source values for Postgres TIMESTAMPTZ binding, but the current fixture tests do not explicitly assert representative timestamp preservation. The original P075 criteria require JSON/time conversion validation, so timestamp handling needs direct coverage.

## Success Criteria
- Migration tests identify representative timestamp columns across task, saga, session, worker lease, outbox, idempotency, and config tables.
- Copy execution tests assert those timestamp values are preserved in target-bound rows.
- If a timestamp normalization helper is needed, it is explicit and covered; otherwise tests document that ISO timestamp strings are deliberately passed through for Postgres binding.
- Existing migration planner/copy/validation/CLI tests still pass.

## Subproblems
- none

## Results
- R100

## Latest Check
C108

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P075/children/P104/README.md
- Ticket T102: problems/P000/children/P024/children/P028/children/P075/children/P104/tickets/T102.md
- Result R100: problems/P000/children/P024/children/P028/children/P075/children/P104/results/R100.md
- Check C108: problems/P000/children/P024/children/P028/children/P075/children/P104/checks/C108.md

## Follow-ups
- none
