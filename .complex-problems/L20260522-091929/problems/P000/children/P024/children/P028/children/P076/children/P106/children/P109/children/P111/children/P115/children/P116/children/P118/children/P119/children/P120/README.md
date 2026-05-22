# Fix Fresh Postgres Schema Init Transaction Handling

## Problem

Queue Service cannot initialize a fresh Postgres database because `init_postgres_schema` catches the expected missing `config` table error but does not roll back the failed transaction before running baseline DDL. Postgres then rejects subsequent DDL with `InFailedSqlTransaction`.

## Success Criteria

- `init_postgres_schema` rolls back after the initial version probe fails on a fresh Postgres database.
- A focused test covers fresh Postgres missing-`config` behavior or an equivalent fake connection that proves rollback happens before baseline DDL.
- Existing Queue Service schema tests still pass.
- The fix is deployed to the api staging checkout.
- Queue Service starts on `api.gradievo.com` using the staging DSN file.
- `/health` and `/ready` pass on `127.0.0.1:19987`.
