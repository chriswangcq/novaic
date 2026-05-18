# P348: Runtime finalize handler inventory

Status: done
Parent: P337
Root: P000
Source Ticket: T336 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P348
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P348/README.md
Ticket(s): T337

## Problem
Map all runtime/task handlers and saga contracts that can process finalize/session-ended/skill-end/recovery completion and identify which ones mutate Cortex, queue state, message claims, or wake/session state.

## Success Criteria
- List live handler/contract files and functions.
- Mark each path as mutating or non-mutating.
- Identify required identity fields for each mutating path.
- Produce implementation targets for the remaining P337 children.

## Subproblems
- none

## Results
- R331

## Latest Check
C352

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P348/README.md
- Ticket T337: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P348/tickets/T337.md
- Result R331: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P348/results/R331.md
- Check C352: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P348/checks/C352.md

## Follow-ups
- none
