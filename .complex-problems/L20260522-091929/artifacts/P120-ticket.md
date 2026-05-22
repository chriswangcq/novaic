# Fresh Postgres Schema Init Transaction Ticket

## Problem Definition

Fresh Queue Service Postgres initialization fails because `init_postgres_schema` probes `config` before it exists, catches the exception, and then continues without rolling back the failed transaction. Postgres keeps the transaction in an aborted state, so the baseline DDL loop fails immediately with `InFailedSqlTransaction`.

## Proposed Solution

1. Patch `queue_service/db/schema.py` so the expected missing-version probe failure rolls back before checking existing tables or running baseline DDL.
2. Add a focused fake-connection test proving rollback happens before the first DDL statement when the initial `config` probe fails.
3. Run the focused Postgres boundary tests.
4. Deploy the patched runtime file to the api staging checkout.
5. Restart Queue Service against the staging DSN file and verify `/health` and `/ready`.

## Acceptance Criteria

- Fresh Postgres initialization no longer leaves the transaction aborted after a missing `config` probe.
- The regression test fails without the rollback fix and passes with it.
- Focused Queue Postgres tests pass locally.
- Api staging Queue Service starts on `127.0.0.1:19987` with Postgres backend.
- Api staging `/health` and `/ready` pass.

## Verification Plan

- Run `PYTHONPATH=.:../novaic-common python3 -m pytest -q tests/test_queue_postgres_boundary.py`.
- On api host, sync or patch `queue_service/db/schema.py` into the clean staging checkout.
- Restart the staging service and capture redacted health/readiness output.

## Risks

- The fake connection must model Postgres transaction failure tightly enough to guard the actual behavior.
- Existing schema-version rejection for non-empty unversioned databases must remain intact.

## Assumptions

- The baseline DDL statements are valid because remote diagnostic replay completed all `POSTGRES_SCHEMA_STATEMENTS` in a clean debug schema.
