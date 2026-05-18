# P387: Cortex operational store generation validation

Status: done
Parent: P385
Root: P000
Source Ticket: T376 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P387
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P387/README.md
Ticket(s): T378

## Problem
`novaic-cortex/novaic_cortex/operational_store.py` still uses raw `int(generation)` in projection and active stack store write paths. These live boundaries need explicit non-negative generation validation.

## Success Criteria
- `upsert_scope_projection` validates generation with the explicit non-negative helper.
- `set_active_stack` validates generation with the explicit non-negative helper.
- Focused Cortex operational store tests reject bool and negative generation inputs for the patched boundaries.
- Existing Cortex context-event tests still pass.
- This belongs under P385 because it closes the Cortex half of the residual live generation coercion list.

## Subproblems
- none

## Results
- R371

## Latest Check
C394

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P387/README.md
- Ticket T378: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P387/tickets/T378.md
- Result R371: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P387/results/R371.md
- Check C394: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P387/checks/C394.md

## Follow-ups
- none
