# T008: Task Execution Engine Extraction

Status: done
Problem: P008

## Objective

Extract task execution protocol from `TaskExecutionHandler` into an explicit
adapter/engine.

## Scope

- `task_queue/workers/task_worker.py`
- New task execution adapter module if needed
- Task worker tests and retry/idempotency tests

## Expected Result

`TaskExecutionHandler` is a small boundary that decodes typed jobs and delegates
to a task execution engine.

## Verification

- Targeted task worker pytest
- Retry/idempotency/concurrency pytest
- Static residue guard

## Execution Notes

- Added `task_queue/workers/task_execution.py` with `TaskExecutionEngine`.
- Added `task_queue/workers/task_metrics.py` so handler and engine share an
  explicit metrics contract without circular imports.
- `TaskExecutionHandler` now decodes typed jobs and delegates execution to
  `engine.execute_with_heartbeat(task)`.
- Updated retry/idempotency tests to replace explicit engine ports.
- Verification: targeted task/engine suite passed (`10 passed`).
