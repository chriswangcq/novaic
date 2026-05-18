# P384: Cortex archive diagnostics source guard classification

Status: done
Parent: P379
Root: P000
Source Ticket: T372 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P379/children/P384
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P379/children/P384/README.md
Ticket(s): T374

## Problem
Cortex source must be scanned for archive diagnostics residue: generation coercion, hidden active-state lookup, top-level versus nested remaining-stack confusion, and projection consuming diagnostic stack as semantic stack.

## Success Criteria
- Source guards are run over Cortex lifecycle/projection/writer files and relevant tests.
- Every guard hit is classified as safe, fixed, or moved to a follow-up problem.
- No live Cortex archive diagnostic path synthesizes diagnostics from hidden active state or coerces bool generation.
- Projection semantics remain explicit: top-level `remaining_stack` is semantic; nested `archive_diagnostics.remaining_stack` is diagnostic only.

## Subproblems
- none

## Results
- R367

## Latest Check
C390

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P379/children/P384/README.md
- Ticket T374: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P379/children/P384/tickets/T374.md
- Result R367: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P379/children/P384/results/R367.md
- Check C390: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P379/children/P384/checks/C390.md

## Follow-ups
- none
