# P340: Session-ended delivery chain inventory

Status: done
Parent: P336
Root: P000
Source Ticket: T327 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P340
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P340/README.md
Ticket(s): T328

## Problem
Before changing behavior, map the exact session-ended/finalize delivery chain and classify which files own payload construction, validation, transport, route schema, repository mutation, and tests. The result must identify every place where generation can be lost, defaulted, inferred, or silently converted.

## Success Criteria
- List every live file/function in the session-ended delivery chain from wake-finalize saga to repository call.
- Identify payload fields required at each boundary: agent id, subagent id, scope id, generation, finalize reason, remaining stack.
- Classify each boundary as safe, unsafe, or test-only.
- Produce concrete implementation targets for the remaining P336 child problems.

## Subproblems
- none

## Results
- R322

## Latest Check
C343

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P340/README.md
- Ticket T328: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P340/tickets/T328.md
- Result R322: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P340/results/R322.md
- Check C343: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P340/checks/C343.md

## Follow-ups
- none
