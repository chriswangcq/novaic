# PR-281 — Session Outbox Wrapper Boundary

Status: Closed

## Goal

Move outbox append/publish wrapper helpers from `SessionRepository` to
`SessionOutboxDispatcher`.

## Scope

- Add dispatcher methods for appending session outbox effects and publishing
  attach/create-wake effects with current normalized return shapes.
- Delete repository helper methods that own outbox append/publish mechanics.
- Keep coordinator flow in `SessionRepository`.

## Acceptance Criteria

- `session_repo.py` contains no `_append_session_outbox_after_transaction`,
  `_publish_session_outbox_effect`, or `_publish_wake_creation_outbox_effect`.
- Outbox append still commits through `SessionLedgerRepository`.
- Wake start, wake restart, and attach transitions all require a durable outbox
  row; missing outbox intent is a hard failure.
- Targeted outbox tests pass.
- Full runtime suite passes.

## Verification

- Targeted PR-281 test.
- `pytest`
- `git diff --check`

## Closure Notes

- Deleted repository-owned outbox append/publish helper methods.
- Repository now persists wake/restart outbox rows atomically through
  `SessionLedgerRepository.record_transition(..., outbox_effect=...)`.
- Kept only the current attach publish helper in `SessionOutboxDispatcher`;
  unused append and synchronous wake publish wrappers were removed after the
  fully queued wake cutover.
- Tightened the transition wrapper so all three outbox-backed transitions pass
  `require_outbox=True`.
- Added `tests/test_pr281_session_outbox_wrapper_boundary.py`.
- Verified by targeted PR-281 residue tests and full runtime suite:
  `pytest` in `novaic-agent-runtime` -> 358 passed.
