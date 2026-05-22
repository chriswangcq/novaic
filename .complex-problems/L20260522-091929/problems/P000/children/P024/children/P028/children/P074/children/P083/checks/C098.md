# P083 Check Not Success

## Summary

R091 solves the route-level transient error handling gap, but the original P083 scope is not fully closed. Worker assembly still catches SQLite-specific startup failures directly, and repository recovery transactions still carry SQLite timeout hints in unbranched code used by the Queue runtime path.

## Blocking Gaps

- `task_queue/workers/assembly_factories.py` still imports `sqlite3` and catches `sqlite3.OperationalError` while retrying startup DB schema connection. This is explicitly part of the original problem's "worker assembly code" residue.
- `queue_service/queue_db.py` and `queue_service/saga_repo.py` still pass `sqlite_busy_timeout_ms=250` directly in recovery transactions. The Postgres adapter ignores this, but the production-facing code path still carries SQLite vocabulary and existing tests currently assert that residue.
- R091's own Known Gaps section states repository-level SQLite timeout hints remain, so the one-go result cannot honestly satisfy "SQLite busy handling remains only in sqlite-specific compatibility branches or tests."

## Result IDs

- R091
