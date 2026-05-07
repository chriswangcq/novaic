# PR-288B — Remaining Observed Event Handlers

Status: Closed

## Goal

Route attach-published, archive-published, publish-failed, finalize-requested,
and watchdog-suspected-dead observations through the same observed-event
handler model.

## Scope

- Add observed event shapes for non wake-created effects.
- Make duplicate observations idempotent.
- Add generation checks for attach/finalize observations.

## Dependencies

- PR-288A.

## Acceptance Criteria

- Non wake-created publisher paths delegate observation handling.
- Tests cover duplicate and stale-generation observations.

## Verification

- Targeted observed event tests.
- Full runtime suite.

## Closure Notes

- Closed after re-scoping by state semantics.
- PR-288B1 closed the real remaining state hazard: active attach now commits
  transition, attach outbox, and input-consumed accounting atomically before
  publish attempts.
- Recovery archive publication and publish failures do not currently mutate
  session FSM state; their durable truth is the outbox row status/attempts, so
  they do not need a separate state-changing observed-event handler at this
  layer.
- Finalize/watchdog state transitions are already represented as explicit
  session events (`session_finalized`, `session_finalize_rejected`,
  `session_suspected_dead`, `session_suspected_dead_observed`).
- Verified by targeted attach/recovery/finalize/outbox tests and full runtime
  suite: `pytest` in `novaic-agent-runtime` -> 357 passed.
