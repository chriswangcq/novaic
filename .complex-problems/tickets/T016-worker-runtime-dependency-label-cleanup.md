# T016: Worker Runtime Dependency Label Cleanup

Status: done
Problem: P016

## Objective

Remove stale `task-sync` and `saga-sync` labels from component worker assembly.

## Scope

- `novaic-agent-runtime/task_queue/workers/worker_assemblies.py`
- Residue tests/static scans as needed.

## Expected Result

Runtime worker IDs/log labels align with live worker names.

## Verification

- Static scan for retired sync labels.
- Worker boundary tests.
