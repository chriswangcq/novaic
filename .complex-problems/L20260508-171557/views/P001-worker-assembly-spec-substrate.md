# P001: Worker Assembly Spec Substrate

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
`worker_assemblies.py` still contains per-worker hand-written lifecycle assembly. Build a component-level assembly spec/interpreter so worker construction is data/spec driven where practical, and displaced manual wiring is deleted or guarded.

## Success Criteria
- A reusable worker assembly spec substrate exists under `task_queue/workers`.
- Existing workers are migrated to the spec interpreter without changing runtime modes.
- `worker_assemblies.py` shrinks to declarations and generic interpretation rather than duplicated lifecycle construction.
- Tests prove registry still wires all worker modes and old direct lifecycle construction cannot creep back.

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
