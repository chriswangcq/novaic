# P122: Inventory Production Queue Runtime And Cutover Preconditions

Status: done
Parent: P077
Root: P000
Source Ticket: T120 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P077/children/P122
Body: problems/P000/children/P024/children/P028/children/P077/children/P122/README.md
Ticket(s): T122

## Problem
Before touching production Queue data, all processes, configs, and credential inputs that can read or write `/opt/novaic/data/queue.db` must be identified. The production Postgres target and rollback plan must be confirmed without exposing credentials.

## Success Criteria
- Production Queue Service, workers, outbox workers, schedulers, and other possible queue writers are listed with process IDs, commands, and owners.
- Current Queue runtime configuration is captured with credential values and credential-file paths redacted.
- Production Postgres target identity is confirmed as intended and non-staging.
- Rollback plan is documented, including SQLite restore/config revert steps and conditions.
- A go/no-go preflight decision is recorded before freeze or backup.

## Subproblems
- none

## Results
- R119

## Latest Check
C134

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P077/children/P122/README.md
- Ticket T122: problems/P000/children/P024/children/P028/children/P077/children/P122/tickets/T122.md
- Result R119: problems/P000/children/P024/children/P028/children/P077/children/P122/results/R119.md
- Check C134: problems/P000/children/P024/children/P028/children/P077/children/P122/checks/C134.md

## Follow-ups
- none
