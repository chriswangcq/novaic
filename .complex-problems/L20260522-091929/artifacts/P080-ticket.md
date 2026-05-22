# Port Task Queue And Idempotency SQL To Postgres

## Problem Definition

`queue_service/queue_db.py` still uses SQLite-oriented task repository SQL and semantics: `datetime(...)` comparisons, `json_each`/`json_extract`, sqlite busy-timeout hints, unique-constraint string matching, and process-local locks as correctness boundaries. The task lifecycle and idempotency ledger must operate correctly on Postgres using JSONB predicates, native `timestamptz` comparisons, explicit row locks or compare-and-update patterns, and Postgres-safe duplicate/idempotency behavior.

## Proposed Solution

Split the task/idempotency port into focused child problems. First add task SQL dialect helpers and Postgres candidate/lock query tests for claim/recovery/cancel. Then port task mutation paths to use explicit task-state locking or compare-and-update semantics. Finally port idempotency ledger acquisition/completion/release/diagnostics to Postgres-safe SQL and exception behavior. Keep real Postgres staging validation for the later staging ticket, but make the generated SQL and fake-boundary behavior explicit and test-covered here.

## Acceptance Criteria

- Task claim query uses Postgres-safe candidate selection and locking, including `FOR UPDATE SKIP LOCKED` or an equivalent explicit compare-and-update pattern.
- Task retry and stale recovery use native timestamptz comparisons rather than SQLite `datetime(...)`.
- Task dependency readiness and cancel-by-agent use JSONB predicates rather than `json_each`/`json_extract`.
- Task publish/complete/fail/heartbeat/release/cancel single-row mutations use explicit task-state locks or compare-and-update semantics under Postgres.
- Task idempotency acquisition/completion/release preserves in-progress, duplicate, completed-result, owner-token, and lease behavior under Postgres transactions.
- Tests cover duplicate claim losers, completion/recovery races or compare-and-update losers, JSONB dependency readiness, cancel-by-agent, and idempotency completed/in-progress cases without production access.

## Verification Plan

Run focused tests for task repository SQL generation and fake Postgres DB behavior, existing task FSM/store tests, selected `TaskQueue` sqlite compatibility tests, and static grep guards for Postgres path removal of `datetime`, `json_each`, `json_extract`, and SQLite busy-timeout assumptions.

## Risks

- Task claim/recovery concurrency is correctness-critical and can appear fine in single-threaded tests; fake-boundary tests must explicitly cover loser/no-candidate behavior.
- Current code serializes JSON text in several task paths; Postgres JSONB must avoid double-encoding.
- Idempotency completion is a side-effect guard; changing it carelessly can duplicate work or lose completed results.
- Full confidence still requires a later real-Postgres staging test.

## Assumptions

- P079's FSM store foundation is available for task event/state/outbox mechanics.
- Saga, session, lease, route-level transient error handling, data migration, and production cutover remain separate tickets.
- SQLite remains useful for existing unit fixtures during the port, but the production Postgres path should not depend on SQLite fallback logic.
