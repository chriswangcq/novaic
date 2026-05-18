# P472: Saga decision config injection

Status: done
Parent: P469
Root: P000
Source Ticket: T462 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P472
Body: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P472/README.md
Ticket(s): T463

## Problem
`react_think.py` and `react_actions.py` currently read `ServiceConfig.MAX_ROUNDS_BEFORE_FORCE_FINALIZE` inside decision adapter functions, and `react_think.py` also reads `ServiceConfig.MAX_STACK_HOLD_RETRIES`. Move these values to an explicit configuration snapshot/provider at the saga or worker assembly boundary so decision construction is deterministic from explicit inputs.

## Success Criteria
- Decision adapter functions no longer directly read `ServiceConfig` for round/stack limits.
- Config values are supplied through an explicit object, provider, or saga context dependency.
- Tests can vary the limits without monkeypatching global `ServiceConfig`.
- Existing finalize/stack-hold behavior remains covered.

## Subproblems
- P475: React saga decision config model
- P476: React saga config wiring
- P477: React saga config tests

## Results
- R460

## Latest Check
C487

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P472/README.md
- Ticket T463: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P472/tickets/T463.md
- Result R460: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P472/results/R460.md
- Check C487: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P472/checks/C487.md

## Follow-ups
- none
