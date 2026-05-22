# Replace Route SQLite Busy Handling With Queue Transient Error Guards

## Problem Definition

Queue HTTP routes still directly import `sqlite3`, catch `sqlite3.OperationalError`, string-match SQLite busy messages, and log `sqlite_busy` from claim/recovery paths. That keeps a misleading SQLite production mental model after Queue Service moved to Postgres-first runtime semantics. The route layer needs an explicit transient error boundary that preserves defer behavior while naming Postgres contention and connection failures accurately.

## Proposed Solution

1. Add a narrow queue transient error classifier outside `routes.py`.
2. Classify Postgres retryable/transient failures by SQLSTATE and safe class-name fallbacks:
   - `40001` serialization failure.
   - `40P01` deadlock detected.
   - `55P03` lock not available / lock timeout.
   - retryable connection and shutdown SQLSTATE classes such as `08*` and selected `57P0*`.
3. Keep SQLite busy/locked recognition inside the classifier as a compatibility branch for local fixtures and old tests.
4. Replace route-level `sqlite3.OperationalError` and `TimeoutError` branches with a shared defer helper that asks the classifier for a reason, logs that reason, and re-raises non-transient failures.
5. Add route and classifier tests for simulated Postgres transient exceptions, timeout behavior, SQLite busy compatibility, and static route guards.

## Acceptance Criteria

- Queue route code no longer imports `sqlite3`, catches `sqlite3.OperationalError`, or hard-codes `reason=sqlite_busy`.
- Postgres transient errors are classified into explicit `pg_*` defer reasons for claim/recovery routes.
- Claim and recovery endpoints still return empty claim/recovery snapshots for retryable contention.
- Existing SQLite busy behavior still works through a sqlite-specific classifier branch for local fixtures/tests.
- Static tests fail if route-level PG-mode code reintroduces SQLite `datetime`, `json_each`, `json_extract`, `rowid`, `sqlite_busy`, or `sqlite3.OperationalError` residue.

## Verification Plan

- Add focused unit tests for the transient classifier using fake Postgres exceptions with `sqlstate` and `diag.sqlstate`.
- Extend claim/recovery route tests with fake Postgres transient exceptions and assert successful defer responses.
- Add a static route guard test for the forbidden SQLite tokens in `queue_service/routes.py`.
- Run the focused route/transient tests plus the existing Queue Postgres boundary and compile checks.

## Risks

- Over-classifying generic operational exceptions could hide real bugs, so classification should require explicit SQLSTATE, known psycopg-style class names, `TimeoutError`, or SQLite busy compatibility.
- Logging reason names become an operational contract; keep them stable and low-cardinality.

## Assumptions

- Route defer behavior means "do not fail the poller/worker claim request for retryable contention"; retries are driven by the caller's normal polling loop.
- Production Postgres runtime should not log `sqlite_busy`; SQLite compatibility is limited to the classifier branch and tests.
