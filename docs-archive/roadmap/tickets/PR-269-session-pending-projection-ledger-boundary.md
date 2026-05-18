# PR-269 — Session Pending Projection Ledger Boundary

Status: Closed

## Goal

Move the `pending_projection_observed` ledger event shape behind `SessionLedgerRepository` so `SessionRepository` does not hand-build pending projection event payloads or idempotency keys.

## Why

Pending projection is a durable ledger observation. The pure projection builder may remain a reusable deterministic function, but the event contract (`event_type`, payload keys, generation, idempotency key) should have one owner: the session ledger adapter.

## Scope

- Add `SessionLedgerRepository.record_pending_projection()`.
- Delegate existing repository pending projection recording to the ledger method.
- Keep projection calculation deterministic from explicit unconsumed input events.
- Add tests for the ledger method and source-residue guard.

## Non-Goals

- Do not redesign pending restart semantics.
- Do not remove pure projection helpers.
- Do not change inbox buffering behavior.

## Acceptance Criteria

- `SessionRepository` no longer contains `event_type="pending_projection_observed"` or `shadow:pending_projection`.
- Ledger tests prove marker, projection payload, generation, and empty projection behavior.
- Existing pending inbox and restart cutover tests pass.
- Full `novaic-agent-runtime` test suite passes.

## Verification

- `pytest tests/test_pr269_session_pending_projection_ledger_boundary.py tests/test_pr241_pending_inbox_projection.py tests/test_pr243_inbox_restart_cutover.py tests/test_pr263_session_pending_projection_boundary.py`
- `pytest`
- `git diff --check`

## Closure Notes

- Added `SessionLedgerRepository.record_pending_projection()`.
- Updated `SessionRepository` to delegate `pending_projection_observed` event shape and idempotency to the ledger adapter.
- Added PR-269 tests for non-empty projection, empty projection, generation, and source-residue guard.
- Verified targeted suite: 11 passed.
- Verified full runtime suite: 307 passed.
- Verified `git diff --check`: clean.
