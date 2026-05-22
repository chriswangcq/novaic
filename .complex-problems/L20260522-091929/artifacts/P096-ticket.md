# Strengthen Session Locking With Behavioral Postgres Race Tests

## Problem Definition

`P093/R085` added the Postgres state-row locking helper and source-order guards, but it still lacks behavioral evidence that the repository paths behave correctly when state is missing, active session state changes before attach, or finalize restarts pending input. The remaining gap is test coverage, not a broad architecture change.

## Proposed Solution

Add deterministic Postgres-mode behavioral tests around `SessionRepository` using lightweight spy/fake ledger and transaction objects. The tests should execute real repository methods and assert observable state transitions, lock ordering, input durability, and attach/finalize outcomes without needing a live Postgres service.

The smallest useful path is:

1. Build a `FakePostgresTransactionDb` whose `backend_name` is `postgres` and whose transaction context records transaction boundaries.
2. Build a session ledger spy that implements the subset of ledger APIs used by `dispatch`, `_record_attach_request_after_transaction`, and `session_ended`, while recording `ensure_state_locked`, `append_input_received`, `get_state`, `record_transition`, and input consumption calls.
3. Add tests for missing-row first dispatch, changed-active attach revalidation, and finalize-with-pending-input restart.
4. Keep source-order guards from `P093`; add these behavioral tests beside them or in a dedicated file.

## Acceptance Criteria

- A behavioral test executes `SessionRepository.dispatch` for a missing state row and proves locking happens before append/input decision and before the start transition records the outbox.
- A behavioral test executes attach revalidation after the active state changes and proves the input is buffered rather than consumed as an attach.
- A behavioral test executes `session_ended` with pending input and proves restart is queued while the pending input remains the authoritative restart source.
- Tests run in Postgres mode through fake/spy objects rather than SQLite fixtures.
- Existing source-order and SQL-shape tests remain intact.

## Verification Plan

- Run the new behavioral test file.
- Run `tests/test_queue_postgres_session_locking.py`, `tests/test_queue_postgres_fsm_store.py`, `tests/test_queue_postgres_boundary.py`, and existing session regression tests.
- Run compile checks for the new/changed test files.

## Risks

- Overly synthetic fakes can become implementation-detail tests. Keep assertions tied to externally meaningful behavior: input append, lock order, transition action, outbox presence, and consumption/buffering.
- If a live Postgres fixture already exists, prefer it; otherwise do not introduce a heavy service dependency just for this focused gap.

## Assumptions

- Deterministic Postgres-mode spy objects are sufficient for this closure because SQL-shape coverage already verifies the store-level `FOR UPDATE` behavior.
- No production code changes should be needed unless the behavioral tests expose a real ordering bug.
