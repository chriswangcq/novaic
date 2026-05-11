# P006: Wake finalize compensation context repair

Status: done
Parent: P002
Root: P000
Package: problems/P000/children/P002/children/P006
Body: problems/P000/children/P002/children/P006/README.md
Ticket(s): T005

## Problem
When `subagent_wake`, `react_think`, or `react_actions` fails, `SagaOrchestrator._build_wake_finalize_compensation_effect` creates a narrow `wake_finalize` context and drops `agent_root_scope_id`, `wake_scope_path`, `session_generation`, `remaining_stack`, and finalize audit metadata. The compensation finalize then treats the wake scope as a root scope and fails before `session_ended`.

## Success Criteria
- Wake-finalize compensation preserves root/path/session generation/remaining stack/round metadata from the failed saga context.
- Regression tests prove the compensation saga context can drive `cortex_scope_end` and `session_ended` payload builders with the correct generation and scope path.
- The implementation does not introduce fallback guesses that hide missing upstream context.

## Subproblems
- none

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/children/P002/children/P006/README.md
- Ticket T005: problems/P000/children/P002/children/P006/tickets/T005.md
- Result R003: problems/P000/children/P002/children/P006/results/R003.md
- Check C003: problems/P000/children/P002/children/P006/checks/C003.md

## Follow-ups
- none
