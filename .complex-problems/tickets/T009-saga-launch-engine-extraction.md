# T009: Saga Launch Engine Extraction

Status: done
Problem: P009

## Objective

Extract saga launch protocol from `SagaLaunchHandler` into an explicit
adapter/engine.

## Scope

- `task_queue/workers/saga_worker.py`
- New saga launch adapter module if needed
- Saga worker tests

## Expected Result

`SagaLaunchHandler` is a small boundary that decodes typed saga jobs and
delegates launch mechanics to `SagaLaunchEngine`.

## Verification

- Targeted saga worker pytest
- Static residue guard

## Execution Notes

- Added `task_queue/workers/saga_launch.py` with `SagaLaunchEngine`.
- Added `task_queue/workers/saga_metrics.py` so handler and engine share an
  explicit metrics contract.
- `SagaLaunchHandler` now decodes typed saga jobs and delegates launch protocol
  to `engine.launch_with_heartbeat(saga)`.
- Verification: targeted saga suite passed (`10 passed`).
