# PR-286 — Wake Creation Durable Outbox Cutover

Status: Closed

## Goal

Make wake saga creation a true durable outbox effect instead of a synchronous
publish inside `SessionRepository.dispatch`.

## Scope

- Dispatch appends input event and wake-create outbox atomically.
- Dispatch returns a queued/pending delivery result when wake creation is not
  yet observed.
- A worker or explicit dispatcher drains wake-create outbox rows.
- Wake activation happens only after a durable observed event.

## Dependencies

- PR-285 FSM decision contract.
- PR-293 return contract if caller-visible delivery names change.

## Risks

- No existing background worker may drain session outbox continuously.
- Current API consumers expect `saga_started` with `saga_id` immediately.
- Crash recovery must not lose queued input.

## Split Criteria

If this ticket requires both worker infrastructure and API contract changes,
split it into smaller tickets before implementation.

## Acceptance Criteria

- `SessionRepository.dispatch` does not synchronously call wake creation publish.
- Wake-create outbox rows are durable and idempotent.
- Observed saga creation transitions session state to active with generation.
- Tests cover crash-before-publish and retry-after-failure.

## Verification

- Durable outbox cutover tests.
- Recovery/rebuild tests.
- Full runtime suite.

## Closure Notes

- Closed through PR-286A, PR-286B, PR-286C, and PR-286D.
- Wake creation is now a durable outbox effect from dispatch/restart. The
  repository returns queued contracts and no longer synchronously creates or
  publishes the wake saga.
- `starting` state is a real occupied state; duplicate inputs buffer until
  wake-created observation activates the planned wake.
- Wake-created observation is generation/scope checked and consumes pending
  input only after activation.
- Verified by targeted child-ticket tests and full runtime suite:
  `pytest` in `novaic-agent-runtime` -> 357 passed.
