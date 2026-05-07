# P016: Worker Runtime Dependency Label Cleanup

Status: done
Parent: P007
Ticket: T016

## Problem

P007 residue audit found `task-sync` and `saga-sync` still used as runtime
dependency worker labels in component assembly. The live worker names have
already moved to `task-worker` and `saga-worker`; keeping stale sync labels
is misleading residue.

## Success Criteria

- Worker runtime dependency labels use live worker names.
- Static scan for retired sync labels returns no production matches.
- Worker boundary tests still pass.

## Result

- Replaced `WorkerRuntimeDependencies.system("task-sync")` with
  `"task-worker"`.
- Replaced `WorkerRuntimeDependencies.system("saga-sync")` with
  `"saga-worker"`.
- Extended residue guard coverage for retired sync labels.

## Check

- Static scan for retired sync labels returned no matches in worker modules or
  residue guard source.
- Targeted worker boundary suite: `14 passed`.
