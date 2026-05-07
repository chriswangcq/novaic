# P003: Lifecycle-Free Business Handlers

Status: done
Parent: P002
Ticket: T003

## Problem

Business worker classes still own worker lifecycle assembly through `run()`,
`shutdown()`, and direct `GenericWorker` / `ConcurrentGenericWorker`
construction. That keeps business code from becoming DSL-shaped.

## Success Criteria

- Business worker modules no longer import or construct `GenericWorker`,
  `ConcurrentGenericWorker`, `WorkerRuntime`, `WorkerRuntimeConfig`,
  `SyntheticJobSource`, `NoopReporter`, or `ShutdownController`.
- Business handler classes expose `handle(job)` and explicit resource cleanup
  only.
- Registry owns GenericWorker/ConcurrentGenericWorker construction for task,
  saga, health, scheduler, and durable outbox workers.
- Old `*WorkerSync.run()` and `*WorkerSync.shutdown()` shapes are deleted, not
  left as compatibility wrappers.
- Tests prove the boundary and runtime behavior.

## Subproblems

- None initially.

## Results

- R003: Business worker modules are lifecycle-free and registry-owned.

## Check

- C003: success

## Follow-ups

- None.
