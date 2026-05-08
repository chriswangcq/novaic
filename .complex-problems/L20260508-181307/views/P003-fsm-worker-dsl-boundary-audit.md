# P003: FSM Worker DSL Boundary Audit

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T003

## Problem
Audit whether the implemented runtime shape matches the documented FSM/worker/DSL architecture: generic FSM substrate, generic worker substrate, declarative roster/assembly specs, pure policy/spec/plan helpers, plan-first effects, and explicit accepted Python computation hooks.

## Success Criteria
- The live code paths named in `runtime-fsm-worker-dsl-status.md` exist and are imported/used consistently.
- The audit verifies action engines delegate behavior calculation to policy/spec/plan helpers where claimed.
- Accepted Python computation hooks are explicitly named and are not hidden fallback paths.
- Any mismatch between documentation and implementation is fixed or converted into a follow-up problem.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T003: problems/P000/children/P003/tickets/T003.md
- Result R002: problems/P000/children/P003/results/R002.md
- Check C002: problems/P000/children/P003/checks/C002.md

## Follow-ups
- none
