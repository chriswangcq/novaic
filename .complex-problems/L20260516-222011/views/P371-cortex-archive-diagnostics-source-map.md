# P371: Cortex Archive Diagnostics Source Map

Status: done
Parent: P368
Root: P000
Source Ticket: T359 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P371
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P371/README.md
Ticket(s): T360

## Problem
Before changing the archive path, identify the exact current functions, request schemas, payload fields, tests, and event writers involved in `CORTEX_SCOPE_END` from wake finalize through Cortex archive/context-event persistence.

## Success Criteria
- Lists the runtime wake-finalize payload builder, task handler, bridge/client, Cortex API request model, archive function, and context-event writer involved.
- Identifies which finalize diagnostics are currently preserved, dropped, inferred, or synthesized.
- Identifies existing tests that should be extended or replaced.
- Produces clear implementation targets for boundary propagation and archive persistence children.

## Subproblems
- none

## Results
- R353

## Latest Check
C376

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P371/README.md
- Ticket T360: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P371/tickets/T360.md
- Result R353: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P371/results/R353.md
- Check C376: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P371/checks/C376.md

## Follow-ups
- none
