# Start Queue Service With Confirmed Postgres Target

## Problem

After startup defaults are clean and a non-production Queue Postgres target is available, Queue Service must actually start in Postgres mode and pass health/readiness. This child belongs under P111 because runtime startup is blocked by environment/credential availability, unlike code cleanup.

## Success Criteria

- A confirmed non-production Queue Postgres target is available before startup.
- Queue Service starts with `NOVAIC_QUEUE_DB_BACKEND=postgres`.
- Startup evidence proves Postgres mode.
- Health/readiness endpoints pass.
- Secrets and DSNs are redacted from artifacts.
