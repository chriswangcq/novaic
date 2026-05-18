# P474: Hidden input remediation tests and guards

Status: done
Parent: P469
Root: P000
Source Ticket: T462 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P474
Body: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P474/README.md
Ticket(s): T468

## Problem
Prove the hidden-input remediation is not just code movement. Focused tests/guards must show saga decisions can be controlled through explicit config and that no direct decision-path `ServiceConfig` read remains.

## Success Criteria
- Add or update focused tests for injected round/stack limits in `react_think` and `react_actions`.
- Run relevant existing tests for session FSM, react saga routing, and hidden-input/residue guards.
- Save test logs under `.complex-problems/L20260516-222011/tmp/p474/`.
- Record any remaining risk explicitly.

## Subproblems
- P478: Rerun hidden input focused tests from correct runtime cwd

## Results
- R462

## Latest Check
C491

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P474/README.md
- Ticket T468: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P474/tickets/T468.md
- Result R462: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P474/results/R462.md
- Check C489: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P474/checks/C489.md
- Check C491: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P474/checks/C491.md

## Follow-ups
- P478: Rerun hidden input focused tests from correct runtime cwd
