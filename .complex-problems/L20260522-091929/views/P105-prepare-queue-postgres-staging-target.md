# P105: Prepare Queue Postgres Staging Target

Status: done
Parent: P076
Root: P000
Source Ticket: T103 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P076/children/P105
Body: problems/P000/children/P024/children/P028/children/P076/children/P105/README.md
Ticket(s): T104

## Problem
P076 needs a non-production Postgres target before any Queue Service smoke can run. The database must be clearly separate from production, initialized with current Queue schema, and optionally seeded or checked with the migration tooling without exposing secrets.

## Success Criteria
- A non-production Queue Postgres DSN or DSN file is identified and redacted in artifacts.
- The target is confirmed non-production and safe to write.
- Current Queue Postgres schema is initialized or verified.
- Initial table counts and config schema version are recorded.
- If migration fixture data is used, the migration report is generated and redacted.
- Missing credentials or environment access are recorded as an explicit blocker with exact next commands.

## Subproblems
- none

## Results
- R101

## Latest Check
C110

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P076/children/P105/README.md
- Ticket T104: problems/P000/children/P024/children/P028/children/P076/children/P105/tickets/T104.md
- Result R101: problems/P000/children/P024/children/P028/children/P076/children/P105/results/R101.md
- Check C110: problems/P000/children/P024/children/P028/children/P076/children/P105/checks/C110.md

## Follow-ups
- none
