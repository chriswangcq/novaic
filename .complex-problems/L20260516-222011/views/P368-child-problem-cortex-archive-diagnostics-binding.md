# P368: Child Problem: Cortex Archive Diagnostics Binding

Status: done
Parent: P338
Root: P000
Source Ticket: T355 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/README.md
Ticket(s): T359

## Problem
Cortex scope archive metadata must not record finalize reason or generation diagnostics for the wrong wake. The archive boundary should rely on explicit payload identity, not active lookup.

## Success Criteria
- Verify or fix `task_queue/handlers/cortex_handlers.py`, wake-finalize payload builders, and Cortex bridge calls.
- Tests prove stale or missing generation cannot archive.
- Tests prove valid archive records the intended reason/generation metadata.
- No direct archive path uses inferred active generation.

## Subproblems
- P371: Cortex Archive Diagnostics Source Map
- P372: Scope End Boundary Contract Propagation
- P373: Cortex Archive Diagnostics Persistence
- P374: Cortex Archive Diagnostics Aggregate Verification

## Results
- R360

## Latest Check
C383

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/README.md
- Ticket T359: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/tickets/T359.md
- Result R360: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/results/R360.md
- Check C383: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/checks/C383.md

## Follow-ups
- none
