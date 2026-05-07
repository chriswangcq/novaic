# PR-330 Task Worker Generic Source

Status: Closed
Phase: 4
Owner: Codex

## Goal

Represent task claiming, heartbeat, completion, and failure reporting through
generic worker source/reporter adapters.

## Scope

- Add `QueueTaskSource` or equivalent.
- Keep Queue Service as Task FSM state authority.
- Model dependency release and heartbeat through explicit adapter methods.

## Deletion Target

- Task worker-owned claim loop and heartbeat lifecycle scaffolding.

## Acceptance

- Task claim/release/complete/fail semantics stay unchanged.
- Heartbeat is component-policy owned or adapter-owned with explicit contract.

## Verification

- Task worker tests.
- Task FSM tests remain passing.

## Closure Notes

Added `TaskQueueJobSource` as the task-specific source adapter for the generic
worker substrate. It owns queue claim attempts and explicit saga dependency
release translation, returning either a ready `queue_task` job or a
`queue_task_dependency_released` no-op job. Queue Service remains the Task FSM
state authority.

Verification:

```bash
pytest -q tests/test_pr330_task_worker_generic_source.py
```
