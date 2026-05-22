# Start Entangled In Postgres Mode For REST Staging

## Problem

After a safe target exists, Entangled must start in Postgres mode and prove readiness without touching the active SQLite file. This belongs under `P051` because REST smokes are only meaningful against a running Postgres-mode service.

## Success Criteria

- A staging/local Entangled process starts with `--db-backend postgres` against the safe target on a non-conflicting loopback port.
- `/v1/health` and `/v1/ready` return success.
- Process arguments show Postgres mode and do not expose secrets.
- File-handle checks show the staging process is not opening active SQLite database files.
- Startup/schema logs are inspected for Postgres DDL or readiness errors.
- The staging process lifecycle is recorded, including cleanup/stop instructions or confirmation.
