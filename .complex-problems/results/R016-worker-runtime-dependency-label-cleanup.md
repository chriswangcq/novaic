# R016: Worker Runtime Dependency Label Cleanup Result

## Outcome

Removed stale sync runtime labels from component worker assembly.

- `task-sync` became `task-worker`.
- `saga-sync` became `saga-worker`.
- Residue guard now includes retired sync labels without embedding literal
  retired strings that would pollute static scans.

## Files Changed

- `novaic-agent-runtime/task_queue/workers/worker_assemblies.py`
- `novaic-agent-runtime/tests/test_pr338_business_handlers_lifecycle_free.py`
