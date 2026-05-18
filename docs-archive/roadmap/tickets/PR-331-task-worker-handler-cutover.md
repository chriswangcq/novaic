# PR-331 Task Worker Handler Cutover

Status: Closed
Phase: 4
Owner: Codex

## Goal

Make task worker business logic a thin handler behind the generic substrate.

## Scope

- Extract task idempotency and handler invocation from the task business
  handler.
- Return explicit `WorkerResult` values.
- Delete displaced lifecycle code.

## Deletion Target

- The retired task worker bespoke lifecycle loop.
- Duplicated shutdown/sleep/exception scaffolding.

## Acceptance

- Task execution behavior is unchanged.
- Business handler does not directly mutate lifecycle tables.
- Generic worker owns loop and shutdown.

## Verification

- Task worker unit tests.
- Integration task tests.

## Closure Notes

Cut the retired task worker loop over to `GenericWorker` and exposed
`TaskExecutionHandler.handle()` as the one-job business handler. Task execution
protocol now lives in `TaskExecutionEngine`, while the component substrate owns
polling, shutdown, sleeping, exception isolation, and loop metrics.

Verification:

```bash
pytest -q tests/test_pr331_task_worker_handler_cutover.py tests/unit/task_queue/test_retry_policy_and_idempotency.py tests/unit/task_queue/test_dedup_guard_failure_path.py tests/unit/task_queue/test_high_concurrency_retry_replay.py
```
