# Remove stale saga optional-step residue

## Problem

The task_queue production residue classification found that `SagaStep.optional`, `add_task_step(optional=...)`, `add_parallel_step(optional=...)`, and `WAKE_FINALIZE_SAGA.add_task_step(... optional=True)` appear to be stale or misleading. The active DAG representation and visible task execution path do not consume task-step optional semantics, so the code advertises behavior that is not actually implemented.

## Success Criteria

- The saga substrate no longer exposes unused or misleading `optional` task/parallel step semantics.
- `wake_finalize.py` no longer passes `optional=True` unless a real implemented optional-step contract exists and is tested.
- Existing saga lifecycle tests are updated to match the cleaned contract.
- Focused tests prove wake_finalize DAG dependencies and saga definition behavior still work after cleanup.
