# PR-333 Saga Worker Handler Cutover

Status: Closed
Phase: 5
Owner: Codex

## Goal

Migrate saga DAG launching into a thin handler behind the generic concurrent
worker substrate.

## Scope

- Add saga source/reporter adapters.
- Extract DAG build + task publish into a handler.
- Remove saga-specific lifecycle threading from business code.

## Deletion Target

- Saga-specific thread bookkeeping, cleanup, and bespoke run loop.

## Acceptance

- Saga launch semantics are unchanged.
- Saga state transitions still go through Queue Service Saga FSM.
- Concurrency is component-owned.

## Verification

- Saga worker tests.
- Saga FSM/integration tests.

## Closure Notes

Cut the retired saga worker loop over to `ConcurrentGenericWorker` and added
`SagaClaimSource`. Saga launch logic is now exposed through
`SagaLaunchHandler.handle()` and `SagaLaunchEngine`, while concurrency and
lifecycle bookkeeping are component-owned. Removed the saga-specific
`_running_sagas` table and bespoke thread cleanup/start methods.

Verification:

```bash
pytest -q tests/test_pr333_saga_worker_handler_cutover.py tests/unit/task_queue/test_saga_worker_boundary.py tests/test_pr310_saga_repository_fsm_cutover.py tests/test_pr313_worker_lease_cutover.py
```
