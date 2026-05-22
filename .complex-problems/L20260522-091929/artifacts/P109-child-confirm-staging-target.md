# Confirm Non-Production Queue Postgres Target

## Problem

P109 needs a confirmed non-production Queue Postgres DSN or DSN file before any Queue Service startup or API smoke can safely run. This child belongs under T106 because target confirmation is the hard safety gate and current evidence shows the local shell lacks `NOVAIC_QUEUE_POSTGRES_DSN_FILE` and `NOVAIC_QUEUE_POSTGRES_DSN`.

## Success Criteria

- A Queue Postgres DSN file or direct DSN is available to the smoke runner.
- The target is confirmed non-production by hostname/database naming, deployment context, or explicit user-provided confirmation.
- The target public identity is recorded with DSNs/secrets redacted.
- If no target can be confirmed, an explicit blocker is recorded with exact environment variables or file path required.
