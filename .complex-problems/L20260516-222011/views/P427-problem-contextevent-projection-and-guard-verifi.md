# P427: Problem: ContextEvent projection and guard verification

Status: done
Parent: P425
Root: P000
Source Ticket: T412 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P425/children/P427
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P425/children/P427/README.md
Ticket(s): T414

## Problem
The most dangerous regression class is tool payloads or image/base64 data leaking back into LLM history/context after the CLI/display contract changes.

## Success Criteria
- Focused Cortex tests pass.
- Guards show no `stable_json(observation)` fallback or history display expansion path.
- Any leakage candidate is fixed or split into a follow-up.

## Subproblems
- none

## Results
- R406

## Latest Check
C432

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P425/children/P427/README.md
- Ticket T414: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P425/children/P427/tickets/T414.md
- Result R406: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P425/children/P427/results/R406.md
- Check C432: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P425/children/P427/checks/C432.md

## Follow-ups
- none
