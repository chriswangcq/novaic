# P004: Audit Cortex context event source cutover

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P004
Body: problems/P000/children/P004/README.md
Ticket(s): T004

## Problem
Find any remaining live code paths where Cortex context preparation, stack lifecycle, step recording, or payload reading still use old DFS/source files as authority instead of the event source/projection model, or keep compatibility branches that can silently reintroduce old behavior.

## Success Criteria
- Inspect context event store/projection/read model, API write endpoints, prepare flow, runtime bridge, and old context_stack modules.
- Classify direct DFS file use as authoritative, projection/debug, test-only, or dead residue.
- Record evidence for any live old source-of-truth path.

## Subproblems
- none

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/children/P004/README.md
- Ticket T004: problems/P000/children/P004/tickets/T004.md
- Result R003: problems/P000/children/P004/results/R003.md
- Check C003: problems/P000/children/P004/checks/C003.md

## Follow-ups
- none
