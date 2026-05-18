# PR-326 Session Outbox Generic Worker

Status: Closed
Phase: 2
Owner: Codex

## Goal

Migrate `session-outbox-worker` to the generic worker substrate.

## Scope

- Add a session outbox source/handler/reporter adapter.
- Replace the bespoke loop in `main_novaic.py`.
- Preserve durable effect dispatch through `SessionOutboxDispatcher`.

## Deletion Target

- Manual `while not stop_requested` loop for `session-outbox-worker`.
- Local ad hoc exception/sleep lifecycle code.

## Acceptance

- Worker remains a visible subprocess.
- Drain semantics and batch size are unchanged.
- No business decision moves into the generic substrate.

## Verification

- Session outbox worker tests.
- Runtime worker startup smoke or focused unit tests.

## Closure Notes

Closed. `session-outbox-worker` now runs through `GenericWorker` with
`SyntheticJobSource`, `SessionOutboxHandler`, and `ResultLoggingReporter`.
The old bespoke drain loop was removed from `main_novaic.py`. Verified with
session outbox worker tests and static entrypoint guards.
