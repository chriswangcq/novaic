# PR-286D1 — Repository No Sync Wake Publish

Status: Closed

## Goal

Delete `SessionRepository`'s direct `publish_wake_creation_effect` calls so
dispatch/session-ended only append durable create-wake effects and return queued
contracts.

## Scope

- Start dispatch path returns `wake_start_queued`.
- Restart path returns `restart_pending`.
- Worker/observed event path is responsible for saga creation and activation.
- Keep pending input unconsumed until wake-created observation.

## Dependencies

- PR-286A.
- PR-286B2A.
- PR-286C1.
- PR-293.

## Acceptance Criteria

- Grep shows no `publish_wake_creation_effect` call in `session_repo.py`.
- Queued dispatch/restart can be completed by draining session outbox.
- Full runtime suite passes.

## Verification

- Outbox cutover tests.
- Residue grep.
- Full runtime suite.

## Closure Notes

- Normal dispatch and restart paths now append durable create-wake outbox rows
  and return queued contracts (`wake_start_queued` / `restart_pending`).
- `SessionRepository` no longer calls `publish_wake_creation_effect`; the
  unused wake sync wrapper was deleted from `SessionOutboxDispatcher`.
- Pending inputs remain unconsumed until wake-created observation activates the
  wake.
- Verified by residue grep, targeted outbox/restart tests, and full runtime
  suite: `pytest` in `novaic-agent-runtime` -> 357 passed.
