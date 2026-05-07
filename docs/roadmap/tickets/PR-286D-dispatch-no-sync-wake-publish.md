# PR-286D — Dispatch No Sync Wake Publish

Status: Closed

## Goal

Delete the active code path where `SessionRepository.dispatch` calls
`publish_wake_creation_effect`.

## Scope

- Remove sync wake publish from dispatch start and restart paths.
- Ensure background/explicit worker is responsible for draining create-wake
  effects.
- Update tests that asserted immediate `saga_started`.

## Dependencies

- PR-286A, PR-286B, PR-286C.
- PR-293 return contract.

## Acceptance Criteria

- Grep shows no `publish_wake_creation_effect` call in `session_repo.py`.
- Queued wake creation still reaches active through worker + observation.
- Full runtime suite passes.

## Verification

- Grep residue guard.
- Full runtime suite.

## Closure Notes

- Closed through PR-286D1 and PR-286D2.
- `SessionRepository` no longer synchronously publishes wake creation for
  dispatch or restart; both paths return queued durable contracts.
- Caller handling was updated so queued wake dispatch is treated as a valid
  durable acknowledgement rather than an unexpected missing saga id.
- The unused `publish_wake_creation_effect` wrapper was removed from
  `SessionOutboxDispatcher`.
- Verified by residue grep and full runtime suite:
  `pytest` in `novaic-agent-runtime` -> 357 passed.
