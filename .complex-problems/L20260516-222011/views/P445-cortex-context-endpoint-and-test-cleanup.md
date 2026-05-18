# P445: Cortex context endpoint and test cleanup

Status: done
Parent: P439
Root: P000
Source Ticket: T429 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P445
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P445/README.md
Ticket(s): T433

## Problem
Cortex context projection endpoints and tests should retain only explicit materialized projection behavior. Any compatibility wording, stale DFS/LLM-history implication, or dead context batch path should be cleaned.

## Success Criteria
- `/v1/context/read|append|batch` endpoint docs/comments/tests use explicit materialized projection language.
- Dead compatibility tests or stale names are removed or renamed.
- Cortex context event API tests pass.
- Prepare-path guards still pass.

## Subproblems
- none

## Results
- R424

## Latest Check
C450

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P445/README.md
- Ticket T433: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P445/tickets/T433.md
- Result R424: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P445/results/R424.md
- Check C450: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/children/P445/checks/C450.md

## Follow-ups
- none
