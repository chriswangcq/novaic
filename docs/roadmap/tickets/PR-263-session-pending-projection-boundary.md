# PR-263 Session Pending Projection Boundary

Status: Closed

## Goal

Move pending inbox projection and restart-source shaping out of
`SessionRepository` into deterministic pure functions.

## Scope

- Add a small `queue_service.session_projection` module.
- Keep pending metadata merge behavior stable:
  - non-message metadata uses latest trigger wins;
  - `message_ids` preserves all unique IDs in arrival order.
- Route pending projection and restart source construction through the new module.
- Delete the repository-private projection helpers.
- Update tests so they target the pure boundary, not private repo methods.

## Out Of Scope

- Full finalize/recovery reducer unification remains a later PR.
- DB schema changes are not needed.
- Wake creation outbox behavior is unchanged.

## Small Tickets

- [x] **FSM-263-A Pure projection module**: add deterministic helpers with no IO.
- [x] **FSM-263-B Repository cutover**: import and use the pure helpers.
- [x] **FSM-263-C Residue deletion**: remove repo projection private helpers and
  private-helper tests.
- [x] **FSM-263-D Tests/review**: add boundary tests, guard scans, and run
  targeted plus full runtime tests.

## Verification

- `pytest tests/test_pr263_session_pending_projection_boundary.py tests/test_pr153_pending_inbox_metadata.py tests/test_pr241_pending_inbox_projection.py tests/test_pr243_inbox_restart_cutover.py tests/test_pr245_suspected_dead_recovery.py tests/test_pr254_finalize_ownership.py`
- Guard scan for `_build_pending_input_projection`,
  `_pending_restart_source_from_projection`, and `_merge_pending_metadata` in
  `queue_service/session_repo.py`.

## Review Result

Pass. `SessionRepository` no longer owns pending inbox projection or restart
source shaping. The behavior is covered by pure boundary tests and existing
restart/recovery/finalize tests.
