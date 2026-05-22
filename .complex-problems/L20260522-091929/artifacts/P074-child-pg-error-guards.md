# Replace SQLite Busy Handling With Postgres Transient Error Guards

## Problem

Queue routes and worker assembly code still import `sqlite3`, string-match SQLite busy/locked errors, log `sqlite_busy`, and use SQLite timeout hints. The Postgres runtime path needs explicit transient PG error classification and static guards so production PG mode does not retain misleading SQLite behavior. This belongs under P074 because repository ports are incomplete unless runtime error semantics match Postgres contention and retry behavior.

## Success Criteria

- Queue PG path classifies retryable/transient Postgres errors explicitly, such as deadlock, serialization failure, lock timeout, and connection-level retryable failures.
- Claim/recovery route defer behavior is preserved for transient PG contention without logging `sqlite_busy` in PG mode.
- SQLite busy handling remains only in sqlite-specific compatibility branches or tests, not in the production Postgres path.
- Static guards or tests catch accidental SQLite `datetime`, `json_each`, `json_extract`, `rowid`, `sqlite_busy`, or `sqlite3.OperationalError` usage in PG-mode paths.
- Focused tests cover route defer behavior under simulated PG transient exceptions and verify sqlite defaults still behave for local fixtures.
