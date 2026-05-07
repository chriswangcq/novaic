# T014: Worker Source Adapter Extraction

Status: done
Problem: P014

## Objective

Move task/saga claim source adapters out of business handler modules and into
component-layer source modules.

## Scope

- `novaic-agent-runtime/task_queue/workers/task_worker.py`
- `novaic-agent-runtime/task_queue/workers/saga_worker.py`
- new source adapter modules under `task_queue/workers/`
- assembly and tests.

## Expected Result

Business handler files no longer define worker source/polling adapters.

## Verification

- Source adapter tests.
- Business DSL boundary static tests.
- Full runtime tests.
