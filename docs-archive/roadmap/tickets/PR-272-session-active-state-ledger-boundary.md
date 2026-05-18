# PR-272 — Session Active State Ledger Boundary

Status: Closed

## Goal

Move direct `SessionStateRecord(state="active", ...)` construction out of `SessionRepository` and `SessionOutboxDispatcher`.

## Why

Active session state row shape is part of the ledger adapter contract. Repo and outbox dispatcher should decide when an active session is observed or created, but the exact state row shape should have one owner.

## Scope

- Add `SessionLedgerRepository.record_active_session()`.
- Use it in startup rebuild and create-wake outbox publication.
- Remove `SessionStateRecord` imports from repo and outbox dispatcher.
- Add source guards and regression tests.

## Non-Goals

- Do not change rebuild source query.
- Do not change create wake race handling.
- Do not remove the generic `upsert_state()` primitive from the ledger adapter.

## Acceptance Criteria

- `SessionRepository` and `SessionOutboxDispatcher` no longer import or construct `SessionStateRecord`.
- Active state row shape is centralized in `SessionLedgerRepository.record_active_session()`.
- Existing rebuild, create wake, and session_state SSOT tests pass.
- Full `novaic-agent-runtime` test suite passes.

## Verification

- `pytest tests/test_pr272_session_active_state_ledger_boundary.py tests/test_pr252_session_state_ssot.py tests/test_pr257_remove_active_sessions_table.py tests/test_pr251_wake_creation_outbox_cutover.py tests/test_pr237_session_outbox_observe.py`
- `pytest`
- `git diff --check`

## Closure Notes

- Added `SessionLedgerRepository.record_active_session()`.
- Updated startup rebuild and create-wake outbox publication to use the ledger active-state boundary.
- Removed `SessionStateRecord` imports from `SessionRepository` and `SessionOutboxDispatcher`.
- Added PR-272 tests for active state shape and source-residue guard.
- Verified targeted suite: 14 passed.
- Verified full runtime suite: 313 passed.
- Verified `git diff --check`: clean.
