# P374: Cortex Archive Diagnostics Aggregate Verification

Status: done
Parent: P368
Root: P000
Source Ticket: T359 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P374
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P374/README.md
Ticket(s): T366

## Problem
After source mapping, boundary propagation, and persistence changes, P368 needs an end-to-end style verification that no old inferred archive diagnostics path remains active.

## Success Criteria
- Runs focused runtime and Cortex tests covering the full scope-end diagnostics path.
- Runs compile checks for changed runtime and Cortex modules.
- Runs residue search for `scope_end`, `finalize_reason`, `session_generation`, `remaining_stack`, archive event writers, and active-generation inference.
- Confirms P368 acceptance criteria are all mapped to evidence.

## Subproblems
- none

## Results
- R359

## Latest Check
C382

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P374/README.md
- Ticket T366: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P374/tickets/T366.md
- Result R359: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P374/results/R359.md
- Check C382: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P374/checks/C382.md

## Follow-ups
- none
