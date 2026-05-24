# P001: Enforce Release Controller-only backend deploy entrypoints in code

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
Release Controller plans and the `deploy` executor do not yet share a hard invocation contract. Direct manual backend and Factory deployment targets are still visible and callable, while the controller does not identify its deploy calls with a run id and namespace. This child exists to make the code and tests enforce controller-only release mutation.

## Success Criteria
- Planner adds controller identity env vars to backend and Factory deploy steps.
- Runner merges step env with the existing environment.
- `deploy` fails fast for direct backend/factory image deployment without controller env metadata.
- Obsolete backend remote-build/legacy deployment targets fail as disabled manual paths.
- Unit/CI tests cover env injection, env merging, and manual path rejection.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R000: problems/P000/children/P001/results/R000.md
- Check C000: problems/P000/children/P001/checks/C000.md

## Follow-ups
- none
