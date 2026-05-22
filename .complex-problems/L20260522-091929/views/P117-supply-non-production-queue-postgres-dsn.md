# P117: Supply Non-Production Queue Postgres DSN

Status: done
Parent: P116
Root: P000
Source Ticket: none (none)
Source Check: C115
Package: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P117
Body: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P117/README.md
Ticket(s): T112

## Problem
Queue Service runtime smoke validation cannot proceed until a confirmed non-production Queue Postgres DSN or DSN file is available to the runner. This follow-up should close the external test-environment prerequisite before attempting service startup again.

## Success Criteria
- A non-production Queue Postgres target is supplied via `NOVAIC_QUEUE_POSTGRES_DSN_FILE` or `NOVAIC_QUEUE_POSTGRES_DSN`.
- The target is confirmed staging/test/non-production before any write.
- DSNs/secrets are not printed into artifacts.
- Queue Service startup can be retried with `NOVAIC_QUEUE_DB_BACKEND=postgres`.

## Subproblems
- none

## Results
- R107

## Latest Check
C116

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P117/README.md
- Ticket T112: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P117/tickets/T112.md
- Result R107: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P117/results/R107.md
- Check C116: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P117/checks/C116.md

## Follow-ups
- none
