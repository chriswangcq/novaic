# P017: Task/Saga Handler Engine Injection

Status: done
Parent: P007
Ticket: T017

## Problem

`TaskExecutionHandler` and `SagaLaunchHandler` no longer own worker lifecycle,
but they still construct Queue/Business clients and protocol engines. For the
business-only DSL shape, handlers should be typed job adapters that receive an
already-built action/protocol engine.

## Success Criteria

- Task and saga handler modules do not import or construct Queue/Business
  client classes.
- Task and saga handlers receive explicit engines/collaborators through
  constructor arguments.
- Component assembly owns client and engine construction and cleanup.
- Existing behavior and tests continue to pass.

## Result

- `TaskExecutionHandler` now receives `TaskExecutionEngine`, metrics, worker
  id, and poll interval explicitly; it no longer constructs queue/business
  clients, retry policy, dependencies, or execution engine.
- `SagaLaunchHandler` now receives `SagaLaunchEngine`, metrics, worker id, and
  poll interval explicitly; it no longer constructs clients, dependencies, or
  launch engine.
- `worker_assemblies.py` owns task/saga client construction, engine
  construction, source wiring, logging closures, and cleanup.
- Boundary guard tests reject protocol client/engine construction in task/saga
  handler modules.

## Check

- Static scan for task/saga client/config constructor tokens in handler modules
  returned no matches.
- Targeted task/saga boundary suite: `24 passed`.
- Full runtime suite: `507 passed`.
