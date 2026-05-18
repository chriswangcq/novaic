# P443: Runtime bridge materialized context helper narrowing

Status: done
Parent: P439
Root: P000
Source Ticket: T429 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P443
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P443/README.md
Ticket(s): T431

## Problem
`CortexBridge.read_context`, `append_context`, and `append_context_batch` are broad names that can be mistaken for authoritative LLM history APIs. They should be narrowed or renamed to materialized projection terminology if they remain.

## Success Criteria
- Runtime bridge helper names make their projection-only role explicit.
- Runtime callers are updated to the new names.
- No LLM prepare path calls the projection helpers.
- Focused runtime tests pass.

## Subproblems
- none

## Results
- R422

## Latest Check
C448

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P443/README.md
- Ticket T431: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P443/tickets/T431.md
- Result R422: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P443/results/R422.md
- Check C448: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P443/checks/C448.md

## Follow-ups
- none
