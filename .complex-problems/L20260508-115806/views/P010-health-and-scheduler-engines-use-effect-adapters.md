# P010: Health and scheduler engines use effect adapters

Status: done
Parent: P001
Root: P000
Package: problems/P000/children/P001/children/P010
Body: problems/P000/children/P001/children/P010/README.md
Ticket(s): T007

## Problem
Health and scheduler engines use effect adapters

## Success Criteria
- HealthRecoveryEngine and ScheduledWakeEngine no longer hold direct HTTP/Business/assembler clients; adapters execute explicit effects

## Subproblems
- P015: Health engine effect adapter migration
- P016: Scheduler engine effect adapter migration
- P017: Health/scheduler boundary guards

## Results
- R008

## Latest Check
C008

## Bodies
- Problem: problems/P000/children/P001/children/P010/README.md
- Ticket T007: problems/P000/children/P001/children/P010/tickets/T007.md
- Result R008: problems/P000/children/P001/children/P010/results/R008.md
- Check C008: problems/P000/children/P001/children/P010/checks/C008.md

## Follow-ups
- none
