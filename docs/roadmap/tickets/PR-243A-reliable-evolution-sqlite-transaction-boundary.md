# PR-243A Reliable Evolution SQLite Transaction Boundary

Status: `[x]`

## Goal

Close the SQLite lock hole exposed while verifying PR-243: shadow input
consumption writes were happening outside the explicit DB transaction boundary,
and thread-local SQLite connection setup repeated database-level WAL
initialization in worker threads.

## Phase Ledger

```text
Phase: FSM-05E verification hardening
Subject: DB transaction boundary for session ledger writes
Old source of truth: implicit SQLite connection/transaction behavior
New source of truth: explicit Database.transaction boundary
Input events: input_received / input_consumed
Decision function: unchanged
State transition: unchanged
Outbox effects: unchanged
Observation events: input_consumed
Generation/idempotency key: unchanged
Shadow drift metric: none
Cutover switch: none
Rollback path: revert PR-243A
Legacy deletion condition: no hidden ledger writes outside transaction
Tests: repeated concurrent dispatch test, runtime full suite, common suite
Docs/guards to update: ticket index and architecture implementation record
```

## Scope

- `novaic-agent-runtime/queue_service/session_repo.py`
- `novaic-common/common/db/database.py`
- `novaic-agent-runtime/tests/test_pr235_session_ledger_shadow.py`

## Small Tickets

- [x] **FSM-05E-V1 Input consumption transaction**: wrap
  `_record_shadow_input_consumed_after_transaction()` in
  `Database.transaction(lock_type="global")`.
- [x] **FSM-05E-V2 SQLite connection setup boundary**: initialize
  `journal_mode=WAL` only during database initialization; thread-local
  connections only set per-connection PRAGMAs.
- [x] **FSM-05E-V3 Historical assertion update**: exclude
  `pending_projection_observed` from PR-235 result-event assertions.
- [x] **FSM-05E-V4 Verification**: prove concurrent dispatch no longer hits
  `database is locked`.

## Explicit Dependency Boundary Review

- Ledger writes now happen inside an explicit repository transaction.
- SQLite connection setup no longer relies on hidden repeated per-thread WAL
  initialization.
- No decision logic changed.

## Review Result

Closed.

- Repeated concurrent dispatch test passed 10 consecutive runs.
- Runtime full suite passed.
- Common suite passed with explicit `PYTHONPATH` including common and runtime.

## Verification

- `for i in 1 2 3 4 5 6 7 8 9 10; do pytest tests/test_pr153_pending_trigger_metadata.py::test_concurrent_dispatches_create_one_active_session_and_one_attachment -q || exit 1; done`
- `pytest`
- `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-common:/Users/wangchaoqun/new-build-novaic/novaic-agent-runtime pytest novaic-common/tests`

## Rollback

Revert this PR to restore previous DB wrapper and input consumption behavior.
