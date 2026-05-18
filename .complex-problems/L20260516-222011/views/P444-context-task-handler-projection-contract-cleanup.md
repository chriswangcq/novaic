# P444: Context task handler projection contract cleanup

Status: done
Parent: P439
Root: P000
Source Ticket: T429 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P444
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P444/README.md
Ticket(s): T432

## Problem
The `context.read` task handler both reads materialized context and appends notification hints. Its contract must be explicit so future code does not treat it as LLM history assembly.

## Success Criteria
- `context.read` handler docs/names/tests state it is notification/projection maintenance, not LLM prepare.
- Notification hint idempotency behavior remains covered.
- Assistant/system context append behavior remains covered.
- Focused context handler tests pass.

## Subproblems
- none

## Results
- R423

## Latest Check
C449

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P444/README.md
- Ticket T432: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P444/tickets/T432.md
- Result R423: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P444/results/R423.md
- Check C449: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P444/checks/C449.md

## Follow-ups
- none
