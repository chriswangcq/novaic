# Run Queue Worker And Outbox Postgres Staging Smokes

## Problem

Queue Service API smokes do not prove workers and outbox workers can run against Postgres mode. Representative worker processes must connect through Queue Service, avoid SQLite queue file usage, and successfully process or drain staging-safe work.

## Success Criteria

- Representative task worker process starts against the staging Queue Service.
- Saga worker or safe saga worker equivalent starts against staging Queue Service.
- Session/saga outbox worker or safe drain equivalent runs against staging Postgres mode.
- Logs/process checks show no new SQLite `queue.db` holder for the staging queue path.
- Worker/outbox outcomes and DB counts are recorded.
