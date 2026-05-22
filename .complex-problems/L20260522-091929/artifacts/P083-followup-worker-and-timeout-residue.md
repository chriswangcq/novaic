# Isolate Worker Startup And Recovery SQLite Busy Residue

## Problem

P083 removed route-level SQLite busy handling, but worker assembly and recovery transaction code still expose SQLite-specific exception handling and timeout hints in production-facing Queue paths. The remaining residue should be moved behind explicit compatibility boundaries so Postgres runtime code has clear transient semantics and old SQLite behavior is retained only where deliberately scoped.

## Success Criteria

- `task_queue/workers/assembly_factories.py` no longer imports `sqlite3` or catches `sqlite3.OperationalError` directly; startup retry uses an explicit transient classifier or backend-aware helper.
- Queue and saga recovery transaction calls no longer pass `sqlite_busy_timeout_ms=250` from unbranched production-facing code; SQLite timeout behavior is isolated behind a named sqlite-only helper or adapter boundary.
- Tests that currently assert raw `sqlite_busy_timeout_ms=250` counts are rewritten to assert the clearer boundary instead.
- Static guards cover worker assembly and recovery paths so `sqlite3.OperationalError`, `sqlite_busy_timeout_ms`, and `reason=sqlite_busy` cannot reappear outside SQLite compatibility/test boundaries.
- Existing startup retry, recovery defer, Queue Postgres boundary, and SQLite compatibility tests still pass.
