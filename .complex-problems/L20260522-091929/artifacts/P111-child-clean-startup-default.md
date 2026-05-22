# Clean Queue Startup Postgres Default

## Problem

Queue Service should not have a stale runtime entrypoint that defaults Queue DB startup to SQLite. This child belongs under P111 because a misleading SQLite default can cause local or staging smoke commands to validate the wrong backend before the real service is even started.

## Success Criteria

- Active Queue Service startup entrypoints default `NOVAIC_QUEUE_DB_BACKEND` to `postgres`.
- SQLite remains available only through explicit selection for tests/adapter use.
- Focused tests guard the default and prevent regression to implicit SQLite fallback.
- The change is small and does not rewrite unrelated startup behavior.
