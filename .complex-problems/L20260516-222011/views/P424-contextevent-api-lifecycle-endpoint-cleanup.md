# P424: ContextEvent API lifecycle endpoint cleanup

Status: done
Parent: P417
Root: P000
Source Ticket: T407 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P424
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P424/README.md
Ticket(s): T411

## Problem
ContextEvent API endpoints that append or prepare context may contain lifecycle compatibility logic that bypasses the event-source model.

## Success Criteria
- Inspect API endpoints that call `ContextEventWriter`, prepare LLM context, write context messages, attach inputs, or close skills.
- Ensure they pass explicit identity and do not infer stale active state from old file layouts.
- Patch dangerous defaulting or hidden lookup behavior if found.
- Add focused API lifecycle tests for changed behavior.
- Run context event API lifecycle/write tests.

## Subproblems
- none

## Results
- R404

## Latest Check
C430

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P424/README.md
- Ticket T411: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P424/tickets/T411.md
- Result R404: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P424/results/R404.md
- Check C430: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P424/checks/C430.md

## Follow-ups
- none
