# PR-266 Session Recovery Boundary

Status: Closed

## Goal

Move suspected-dead recovery marker, recovered dispatch metadata, and recovery
archive effect shaping out of `SessionRepository` into deterministic pure
helpers.

## Scope

- Add `queue_service.session_recovery`.
- Keep existing recovery context and archive task payload shapes stable.
- Inject the recovery archive `effect_type` from the repository boundary.
- Remove recovery marker/archive shaping private helpers from
  `SessionRepository`.
- Add pure boundary tests and guard scans.

## Out Of Scope

- Watchdog event production remains unchanged.
- Durable outbox publishing remains unchanged.
- DB schema changes are not needed.

## Small Tickets

- [x] **FSM-266-A Pure recovery helpers**: add marker, dispatch metadata, and
  archive effect builders.
- [x] **FSM-266-B Repository cutover**: route recovery dispatch through helpers.
- [x] **FSM-266-C Residue deletion**: remove repo recovery shaping helpers.
- [x] **FSM-266-D Verification**: run recovery targeted tests and full runtime
  tests.

## Verification

- `pytest tests/test_pr266_session_recovery_boundary.py tests/test_pr245_suspected_dead_recovery.py tests/test_pr247_recovery_outbox_cutover.py tests/test_pr233_active_inbox_dispatch.py`
- Full runtime `pytest`.

## Review Result

Pass. Recovery marker creation, recovered dispatch metadata, and recovery archive
outbox payload construction now live in `queue_service.session_recovery`.
`SessionRepository` consumes the shaped values and no longer owns the recovery
JSON decoding or payload construction.
