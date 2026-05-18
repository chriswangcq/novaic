# PR-327 Saga Outbox Generic Worker

Status: Closed
Phase: 2
Owner: Codex

## Goal

Migrate `saga-outbox-worker` to the generic worker substrate.

## Scope

- Add a saga outbox source/handler/reporter adapter.
- Replace the bespoke loop in `main_novaic.py`.
- Preserve durable effect dispatch through `SagaOrchestrator`.

## Deletion Target

- Manual `while not stop_requested` loop for `saga-outbox-worker`.
- Local ad hoc exception/sleep lifecycle code.

## Acceptance

- Worker remains a visible subprocess.
- Drain semantics and batch size are unchanged.
- Saga FSM remains the owner of saga lifecycle decisions.

## Verification

- Saga outbox worker tests.
- Runtime worker startup smoke or focused unit tests.

## Closure Notes

Closed. `saga-outbox-worker` now runs through `GenericWorker` with
`SyntheticJobSource`, `SagaOutboxHandler`, and `ResultLoggingReporter`.
The old bespoke drain loop was removed from `main_novaic.py`. Verified with
saga outbox handler tests and static entrypoint guards.
