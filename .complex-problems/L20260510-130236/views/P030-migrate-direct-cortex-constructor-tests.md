# P030: Migrate Direct Cortex Constructor Tests

Status: done
Parent: P028
Root: P000
Package: problems/P000/children/P019/children/P023/children/P028/children/P030
Body: problems/P000/children/P019/children/P023/children/P028/children/P030/README.md
Ticket(s): T029

## Problem
Many tests still call `Cortex(MemoryStore(), agent_id)` or `Cortex(store, agent_id=...)`. Runtime no longer supports that path. This belongs under P028 because tests must prove the runtime uses `Cortex(workspace=...)` and not direct store construction.

## Success Criteria
- All Cortex runtime tests construct a Workspace explicitly and call `Cortex(workspace=...)`.
- No `Cortex(MemoryStore`, `Cortex(store`, or positional `Cortex(` store constructor remains in tests.
- Targeted runtime/tool/hook tests pass.

## Subproblems
- none

## Results
- R026

## Latest Check
C026

## Bodies
- Problem: problems/P000/children/P019/children/P023/children/P028/children/P030/README.md
- Ticket T029: problems/P000/children/P019/children/P023/children/P028/children/P030/tickets/T029.md
- Result R026: problems/P000/children/P019/children/P023/children/P028/children/P030/results/R026.md
- Check C026: problems/P000/children/P019/children/P023/children/P028/children/P030/checks/C026.md

## Follow-ups
- none
