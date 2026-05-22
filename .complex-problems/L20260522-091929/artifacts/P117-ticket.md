# Supply Queue Staging DSN Ticket

## Problem Definition

Queue Service Postgres runtime validation is blocked because the runner does not have a confirmed non-production Queue Postgres target. P117 exists to acquire or confirm that target before service startup is retried.

## Proposed Solution

1. Prefer a DSN file to avoid shell-history leakage:
   - set `NOVAIC_QUEUE_POSTGRES_DSN_FILE=/absolute/path/to/non-production-queue-postgres.dsn`.
2. If a DSN file is not practical, use direct DSN:
   - set `NOVAIC_QUEUE_POSTGRES_DSN`.
3. Require explicit non-production confirmation:
   - database/host name clearly indicates staging/test/dev; or
   - the user confirms the target is non-production.
4. Record only redacted public identity and set/unset status.
5. Once supplied, hand control back to the startup/smoke ticket with `NOVAIC_QUEUE_DB_BACKEND=postgres`.

## Acceptance Criteria

- A Queue Postgres DSN file or direct DSN is available to the runner.
- The target is confirmed non-production before any write.
- DSNs/secrets are not printed into artifacts.
- The next Queue Service startup attempt has exact environment variables to use.

## Verification Plan

- Check env var set/unset status without printing values.
- If using `NOVAIC_QUEUE_POSTGRES_DSN_FILE`, verify the file path exists without dumping contents.
- Confirm non-production identity by safe public fields or explicit user confirmation.
- Do not start Queue Service in this ticket; only close the target prerequisite.

## Risks

- Direct DSN can leak through shell history; file-based input is preferred.
- A staging-looking name is not enough if the user/deployment context says otherwise.

## Assumptions

- The user can provide either a DSN file path on this machine or a confirmed staging/test database connection string.
