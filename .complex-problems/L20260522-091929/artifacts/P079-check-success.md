# Queue Postgres FSM Store Foundation Verified

## Summary

P079 is successful. Result `R073` adds the Postgres-aware FSM store foundation needed by later repository ports while preserving existing sqlite fixtures. The foundation now has explicit backend-aware behavior for JSON values, deterministic ordering, mutation transaction requirements, unique-violation detection, and SQLite busy retry isolation.

## Evidence

- `novaic-agent-runtime/queue_service/fsm/sqlite_store.py` records `db.backend_name`, defaulting to `sqlite`, and branches Postgres behavior from sqlite behavior.
- Postgres FSM mutations require an explicit transaction before executing mutating SQL.
- Postgres JSON payload/outbox values are passed as native dict-compatible values instead of sqlite JSON text strings.
- Postgres event/outbox candidate ordering uses `created_at, id` or `created_at DESC, id DESC`; tests assert no `rowid` in generated PG SQL.
- Postgres unique violations are detected by SQLSTATE `23505` or `UniqueViolation`, not SQLite unique-string matching.
- Postgres path does not retry SQLite busy-looking errors; tests prove only one execution attempt.
- Verification passed: 50 selected Queue tests including new Postgres FSM store tests and existing sqlite FSM store/runner tests.

## Criteria Map

- Queue Postgres FSM store or dialect layer exists without relying on SQLite PRAGMAs, `rowid`, or SQLite busy string retries -> backend-aware FSM store behavior and `tests/test_queue_postgres_fsm_store.py` cover no-rowid ordering and no SQLite busy retry in PG path.
- Event/state/outbox append, upsert, list, mark-consumed, and claim-style operations have Postgres-safe SQL forms or separated branches -> generic store uses the same safe qmark SQL through the Queue Postgres adapter, separates PG mutation/ordering/JSON behavior, and preserves sqlite behavior for existing fixtures; pending outbox candidate listing is covered by the new tests.
- Ordering previously using `rowid` is replaced in the Postgres path with deterministic stable keys -> `latest_event`, unconsumed event lists, and pending outbox list use `created_at/id` ordering in PG path and are tested.
- JSONB and timestamptz values are bound/decoded at repository boundary without preserving long-term JSON text assumptions in the Postgres path -> payload/outbox JSON values stay native for PG binding and decoding accepts native dict/list values. Saga-specific state JSON conversion remains a later repository child, which is non-blocking for this foundation.
- Focused tests cover generated SQL/behavior and prove existing sqlite unit fixtures still pass -> 50 selected tests passed, including new PG FSM store tests and existing sqlite FSM store/runner tests.

## Execution Map

- T076 / R073 -> implemented backend-aware FSM store behavior and focused tests for Postgres JSON values, transaction requirements, ordering, unique violation fallback, and busy retry isolation.

## Stress Test

- Failure mode: PG path still silently uses SQLite `rowid` ordering. The new test calls latest event, unconsumed event, all unconsumed events, and pending outbox listing, then asserts no `rowid` and exact `created_at/id` ordering.
- Failure mode: PG path catches and retries a SQLite busy-looking error. The new test raises `RuntimeError("database is locked")` from a PG backend and verifies there is only one execution attempt.
- Failure mode: sqlite fixtures regress while adding PG behavior. Existing generic FSM store and transition runner tests still pass.

## Residual Risk

- Repository-specific row locks, claim/recovery SQL, saga state JSON columns, session/outbox claim semantics, and PG transient route handling are still pending in P080-P083. They are intentionally outside the P079 foundation and remain blocking for the parent P074, not for this child.

## Result IDs

- R073
