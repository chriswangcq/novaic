# Start Queue Service In Postgres Mode

## Problem

After a safe target is confirmed, Queue Service must start as a real runtime in Postgres mode without silently falling back to SQLite. This child belongs under T106 because service startup failure is distinct from both credential discovery and endpoint behavior.

## Success Criteria

- Queue Service is started with `NOVAIC_QUEUE_DB_BACKEND=postgres`.
- Startup logs or runtime public info prove the Postgres backend is active.
- Required auth/bind settings are recorded without secrets.
- Health/readiness endpoints are reachable.
- No SQLite database path is used for the smoke runtime.
