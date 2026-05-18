# P540: Remove stale saga optional-step residue

Status: done
Parent: P538
Root: P000
Source Ticket: none (none)
Source Check: C559
Package: problems/P000/children/P004/children/P281/children/P512/children/P532/children/P534/children/P538/children/P540
Body: problems/P000/children/P004/children/P281/children/P512/children/P532/children/P534/children/P538/children/P540/README.md
Ticket(s): T533

## Problem
The task_queue production residue classification found that `SagaStep.optional`, `add_task_step(optional=...)`, `add_parallel_step(optional=...)`, and `WAKE_FINALIZE_SAGA.add_task_step(... optional=True)` appear to be stale or misleading. The active DAG representation and visible task execution path do not consume task-step optional semantics, so the code advertises behavior that is not actually implemented.

## Success Criteria
- The saga substrate no longer exposes unused or misleading `optional` task/parallel step semantics.
- `wake_finalize.py` no longer passes `optional=True` unless a real implemented optional-step contract exists and is tested.
- Existing saga lifecycle tests are updated to match the cleaned contract.
- Focused tests prove wake_finalize DAG dependencies and saga definition behavior still work after cleanup.

## Subproblems
- none

## Results
- R527

## Latest Check
C560

## Bodies
- Problem: problems/P000/children/P004/children/P281/children/P512/children/P532/children/P534/children/P538/children/P540/README.md
- Ticket T533: problems/P000/children/P004/children/P281/children/P512/children/P532/children/P534/children/P538/children/P540/tickets/T533.md
- Result R527: problems/P000/children/P004/children/P281/children/P512/children/P532/children/P534/children/P538/children/P540/results/R527.md
- Check C560: problems/P000/children/P004/children/P281/children/P512/children/P532/children/P534/children/P538/children/P540/checks/C560.md

## Follow-ups
- none
