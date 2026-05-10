# P026: Phase 3B2 Follow-up Nested And Restart Projection Verification

Status: done
Parent: P023
Root: P000
Package: problems/P000/children/P004/children/P018/children/P023/children/P026
Body: problems/P000/children/P004/children/P018/children/P023/children/P026/README.md
Ticket(s): T019

## Problem
Phase 3B2 writes active-stack projections on successful skill_begin and skill_end, but the check found insufficient direct verification for two original criteria: nested begin/end stack state and restart-like store reuse. Close this by adding focused tests that prove nested API lifecycle projection behavior and persisted SQLite projection readability after constructing a fresh operational store on the same database path.

## Success Criteria
- API lifecycle test opens two nested child skills and verifies the SQLite active-stack frames are top-first after each begin.
- API lifecycle test closes the inner child and verifies the SQLite active-stack projection pops only that child while retaining the outer child and wake.
- A restart-like test reads the same active-stack projection from a new operational store instance using the same SQLite database path.
- Targeted tests and full `novaic-cortex/tests` pass.

## Subproblems
- none

## Results
- R016

## Latest Check
C017

## Bodies
- Problem: problems/P000/children/P004/children/P018/children/P023/children/P026/README.md
- Ticket T019: problems/P000/children/P004/children/P018/children/P023/children/P026/tickets/T019.md
- Result R016: problems/P000/children/P004/children/P018/children/P023/children/P026/results/R016.md
- Check C017: problems/P000/children/P004/children/P018/children/P023/children/P026/checks/C017.md

## Follow-ups
- none
