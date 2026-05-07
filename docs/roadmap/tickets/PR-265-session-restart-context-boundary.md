# PR-265 Session Restart Context Boundary

Status: Closed

## Goal

Move pending-inbox restart saga context shaping out of
`SessionRepository.session_ended()` into a deterministic pure helper.

## Scope

- Add a pure restart context helper near the pending projection code.
- Preserve the current saga context shape:
  - `agent_id`, `subagent_id`, `user_id`, `scope_id`, `session_generation`;
  - normalized `trigger_type`;
  - decoded pending metadata;
  - explicit `finalize` payload.
- Route `SessionRepository` through the helper.
- Add tests pinning metadata decode and context shape.

## Out Of Scope

- Durable outbox creation remains in `SessionRepository`.
- Recovery dispatch metadata shaping remains a later cleanup slice.

## Small Tickets

- [x] **FSM-265-A Pure restart context helper**: add context and metadata result.
- [x] **FSM-265-B Repository cutover**: use helper in `session_ended()`.
- [x] **FSM-265-C Tests/residue**: pin shape and guard repo no longer decodes
  pending restart metadata inline.
- [x] **FSM-265-D Verification**: run targeted plus full runtime tests.

## Verification

- `pytest tests/test_pr265_session_restart_context_boundary.py tests/test_pr243_inbox_restart_cutover.py tests/test_pr254_finalize_ownership.py`
- Full runtime `pytest`.

## Review Result

Pass. Pending restart saga context construction now lives in
`queue_service.session_projection.build_pending_restart_saga()`. The repository
no longer decodes pending restart metadata or normalizes the pending trigger
type inline.
