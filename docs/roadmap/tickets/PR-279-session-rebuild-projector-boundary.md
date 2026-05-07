# PR-279 — Session Rebuild Projector Boundary

Status: Closed

## Goal

Move startup session-state rebuild from `SessionRepository` into a named
projector/adapter.

## Scope

- Add a `session_rebuild` module for rebuilding active session state from
  running/launched saga rows.
- Make `SessionRepository.rebuild()` delegate to that module.
- Add guard coverage that the repository no longer queries `tq_sagas`.

## Acceptance Criteria

- `session_repo.py` contains no `SELECT id, context FROM tq_sagas`.
- Rebuild behavior stays unchanged.
- Targeted rebuild/session tests pass.
- Full runtime suite passes.

## Verification

- Targeted PR-279 test.
- `pytest`
- `git diff --check`

## Closure Notes

- Added `queue_service/session_rebuild.py` as the startup projector/adapter.
- `SessionRepository.rebuild()` now delegates to
  `rebuild_active_sessions_from_sagas`.
- Added `tests/test_pr279_session_rebuild_projector_boundary.py`.
- Updated the final residue guard so active-state rebuilding is owned by the
  rebuild projector and outbox dispatcher, not the repository.
- Targeted rebuild/residue tests passed: 12 passed.
