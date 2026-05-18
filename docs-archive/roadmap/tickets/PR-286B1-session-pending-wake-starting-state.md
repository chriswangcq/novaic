# PR-286B1 — Pending Wake Uses Starting State

Status: Closed

## Goal

When wake creation publication is deferred, record the session as `starting`
instead of `no_active` so a new user message cannot be mistaken for a fresh
session start.

## Scope

- Dispatch publish failure returns `wake_start_queued`.
- Session restart publish failure keeps `restart_pending` but records
  `starting`.
- `record_transition` retains scope id for lifecycle states that are not
  active.

## Dependencies

- PR-283 state taxonomy.
- PR-293 return contract.

## Acceptance Criteria

- Pending wake start state is `starting`.
- Pending wake start has a durable outbox id and scope id.
- A state row in `starting` is not treated as active for attach.

## Verification

- Targeted wake creation failure test.
- State taxonomy tests.

## Closure Notes

- Changed wake creation publish-deferred dispatch result to
  `wake_start_queued`.
- Pending wake creation now records session state as `starting` with the planned
  scope id retained.
- Pending restart publication now records `starting` instead of `no_active`.
- Updated ledger transition persistence so non-active lifecycle states can
  retain scope id while still not being listed as active.
- Updated wake creation failure test.
- Verified with targeted wake/state/ledger tests: 11 passed.
