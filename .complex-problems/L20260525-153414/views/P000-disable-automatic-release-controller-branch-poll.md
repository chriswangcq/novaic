# P000: Disable automatic Release Controller branch polling

Status: done
Parent: none
Root: P000
Source Ticket: none (none)
Source Check: none
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
The live Release Controller currently runs autonomous branch polling, so pushes to main can trigger staging CI/CD without an explicit agent/operator release action. For the current agent-driven workflow, CI/CD should be a centralized service flow, but it should start only from explicit Release Controller API requests.

## Success Criteria
- Live Release Controller has autonomous polling disabled and reports polling.enabled=false/running=false.
- Repository docs describe explicit trigger-based staging CI/CD as the normal path.
- Repository guards fail if sample config or docs reintroduce autonomous polling as the normal backend/factory release path.
- Existing Release Controller unit/CI guard tests pass.
- A subsequent push to main does not auto-start a new release run.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R000: problems/P000/results/R000.md
- Check C000: problems/P000/checks/C000.md

## Follow-ups
- none
