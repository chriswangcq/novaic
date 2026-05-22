# Port Session State Locking And Transition Semantics To Postgres

## Problem Definition

`SessionRepository.dispatch`, attach recording, and `session_ended` currently rely on a database transaction named `global` plus store behavior that was designed around SQLite. In Postgres, decisions for the same `session_key` must serialize on an explicit session state row or equivalent compare/update boundary so first dispatch, attach revalidation, finalization, and restart planning cannot lose inputs or create two active sessions.

## Proposed Solution

Add a Postgres-aware session state serialization helper at the session ledger/store boundary:

1. Ensure a `tq_session_state` row exists for `session_key` before a Postgres session decision reads active state.
2. Lock that row with Postgres `FOR UPDATE` for dispatch, attach revalidation, and finalize/restart decisions.
3. Keep SQLite behavior behind the store adapter so legacy tests still use the existing SQLite transaction shape without leaking SQLite synchronization into Postgres business flow.
4. Revalidate attach and finalize inputs under the locked state row before consuming input events or queueing restart outbox effects.
5. Add focused Postgres-path tests that assert the SQL/adapter behavior for first-dispatch row creation, row locking, attach revalidation, finalize pending-input handling, and no SQLite-only lock assumptions in session business code.

## Acceptance Criteria

- Postgres dispatch ensures and locks `tq_session_state(session_key)` before reading active state or deciding start/attach/buffer/recovery.
- Postgres attach revalidation locks the same session state row before comparing active saga/scope/generation and consuming input.
- Postgres finalization locks the session state row before accepting/rejecting finalize and before deciding close or restart from pending inputs.
- Pending inputs remain append-only durable facts until the locked transition explicitly consumes them.
- Focused tests cover Postgres ensure-and-lock SQL, first-dispatch missing-row behavior, attach revalidation, finalize restart/no-input-loss behavior, and SQLite isolation.
- Existing SQLite session tests continue to pass without adding new production fallback branches.

## Verification Plan

- Add focused unit tests with a Postgres spy/fake store for the new ensure-lock helper and call sites.
- Run the new tests plus existing `test_pr252_session_state_ssot`, `test_pr241_pending_inbox_projection`, `test_pr270_session_finalize_ledger_boundary`, `test_pr273_session_harness_final_residue_guard`, and queue Postgres boundary tests.
- Run compile checks for `queue_service/session_repo.py`, `queue_service/session_ledger.py`, and the FSM store module touched by the helper.
- Inspect diffs for SQLite transaction/path assumptions in session business logic.

## Risks

- Creating a default `no_active` state row too eagerly can overwrite meaningful state if implemented with upsert instead of insert-if-missing.
- Locking after input consumption decisions would still leave a race; the helper must run before active-state decisions.
- Reusing SQLite global transaction wording can hide Postgres semantics from future maintainers.

## Assumptions

- Session state row creation can use `generation=0`, `state='no_active'`, and the dispatch identity for missing rows.
- The existing ledger/store abstraction is the right place to hide SQL dialect differences.
- Tests can validate Postgres behavior through rendered SQL and spy adapters before requiring a live Postgres service in this narrow slice.
