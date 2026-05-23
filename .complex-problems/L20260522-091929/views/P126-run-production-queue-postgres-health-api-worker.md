# P126: Run Production Queue Postgres Health API Worker And Outbox Smokes

Status: done
Parent: P077
Root: P000
Source Ticket: T120 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P077/children/P126
Body: problems/P000/children/P024/children/P028/children/P077/children/P126/README.md
Ticket(s): T133

## Problem
Production Postgres mode must be verified with safe smoke checks after restart. The checks must prove health/readiness, representative Queue APIs, worker startup, and outbox drain behavior without unsafe business side effects.

## Success Criteria
- Health/readiness checks pass in production Postgres mode.
- Safe task API smoke covers publish/claim/complete/fail or an approved production-safe equivalent.
- Safe saga/session/idempotency smoke covers representative lifecycle behavior or documented safe equivalents.
- Worker and outbox process checks show startup and no tracebacks/error loops.
- Post-smoke DB counts and outbox histograms are recorded.
- Smoke artifacts are redacted.

## Subproblems
- none

## Results
- R130

## Latest Check
C145

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P077/children/P126/README.md
- Ticket T133: problems/P000/children/P024/children/P028/children/P077/children/P126/tickets/T133.md
- Result R130: problems/P000/children/P024/children/P028/children/P077/children/P126/results/R130.md
- Check C145: problems/P000/children/P024/children/P028/children/P077/children/P126/checks/C145.md

## Follow-ups
- none
