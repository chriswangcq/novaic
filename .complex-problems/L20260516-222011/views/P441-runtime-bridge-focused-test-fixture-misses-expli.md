# P441: Runtime bridge focused test fixture misses explicit session_generation

Status: done
Parent: P437
Root: P000
Source Ticket: T426 (spawn)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P437/children/P441
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P437/children/P441/README.md
Ticket(s): T427

## Problem
The P437 focused runtime bridge test suite fails because `tests/test_pr85_llm_context_smoke_guardrails.py::test_tool_result_step_preserves_tool_call_id_and_step_ref` builds a React actions context without explicit `session_generation`. Production code correctly requires explicit positive session generation, so the test fixture is stale.

## Success Criteria
- The failing test fixture passes explicit positive `session_generation`.
- The focused runtime bridge test suite used by P437 passes.
- The change does not loosen the production explicit generation validator.

## Subproblems
- none

## Results
- R418

## Latest Check
C444

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P437/children/P441/README.md
- Ticket T427: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P437/children/P441/tickets/T427.md
- Result R418: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P437/children/P441/results/R418.md
- Check C444: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P437/children/P441/checks/C444.md

## Follow-ups
- none
