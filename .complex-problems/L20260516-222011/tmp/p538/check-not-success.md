# P538 check: classification found unresolved risky residue

## Summary

R526 classified all 45 task_queue production hits across 14 files, but the problem is not fully solved because the classification identified follow-up-worthy risky residue: `SagaStep.optional` and `add_*_step(optional=...)` appear to be stale unimplemented saga substrate semantics, and `wake_finalize.py` still uses `optional=True`.

## Blocking Gaps

- P538 success criteria require risky residue to become follow-up. R526 found one concrete risky residue but did not fix it.
- The gap is not just wording: `SagaDefinition.to_dag()` does not propagate `optional` into `DagNode`, and the visible task execution path does not consume task-step optional semantics. Keeping the field/call-site can mislead future code into believing `cortex_scope_end` is allowed to fail while the current DAG dependency chain still treats it as a normal predecessor.

## Result IDs

- R526
