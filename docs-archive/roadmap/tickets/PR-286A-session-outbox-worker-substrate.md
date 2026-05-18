# PR-286A — Session Outbox Worker Substrate

Status: Closed

## Goal

Add a small reusable worker substrate for draining session outbox effects so
dispatch does not need to publish wake creation synchronously.

## Scope

- Add a non-business `SessionOutboxWorker` wrapper around
  `SessionOutboxDispatcher.drain_pending`.
- Keep dependencies explicit: dispatcher, effect types, batch size, clock/sleep
  if looping is introduced.
- Add tests for one-shot drain behavior without changing dispatch semantics.

## Dependencies

- Existing `SessionOutboxDispatcher`.

## Acceptance Criteria

- Worker can drain a bounded batch of pending session outbox rows.
- Worker does not own business decisions or mutate state beyond dispatcher
  behavior.
- Startup wiring was intentionally out of scope for this substrate ticket and
  is now closed by [PR-302](PR-302-session-outbox-worker-production-wiring.md).

## Verification

- Targeted worker tests.

## Closure Notes

- Added `queue_service/session_outbox_worker.py`.
- Added `SessionOutboxWorkerConfig` and `SessionOutboxWorker.drain_once`.
- Worker delegates to `SessionOutboxDispatcher.drain_pending` with explicit
  effect types, session key, and bounded batch size.
- Added `tests/test_pr286a_session_outbox_worker.py`.
- Verified with targeted worker/outbox retry tests: 4 passed.
- Production startup wiring landed later in
  [PR-302](PR-302-session-outbox-worker-production-wiring.md).
