# P031: Phase 3C2 Context Status SQLite Stack Read Cutover

Status: done
Parent: P019
Root: P000
Package: problems/P000/children/P004/children/P019/children/P031
Body: problems/P000/children/P004/children/P019/children/P031/README.md
Ticket(s): T027

## Problem
`context_status` default stack output still uses file-walk stack collection. It must read stack frames from the SQLite active-stack projection while preserving the existing response shape and leaving `include_usage=True` semantic context assembly unchanged.

## Success Criteria
- `context_status(include_usage=False)` returns stack frames from SQLite active-stack projection.
- Empty projection returns the existing empty stack response shape.
- `context_status(include_usage=True)` remains semantic ContextEvent read-model based.
- Tests prove status reads persisted SQLite projection rather than walking scope files.

## Subproblems
- none

## Results
- R024

## Latest Check
C026

## Bodies
- Problem: problems/P000/children/P004/children/P019/children/P031/README.md
- Ticket T027: problems/P000/children/P004/children/P019/children/P031/tickets/T027.md
- Result R024: problems/P000/children/P004/children/P019/children/P031/results/R024.md
- Check C026: problems/P000/children/P004/children/P019/children/P031/checks/C026.md

## Follow-ups
- none
