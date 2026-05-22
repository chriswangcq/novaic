# Queue Postgres Post-Smoke Counts Ticket

## Problem Definition

After the Queue API smoke run, the ledger needs durable post-smoke table counts and redacted target identity evidence so parent problems can prove the smoke wrote to the intended staging Postgres database.

## Proposed Solution

1. Re-query the staging Postgres container for table counts after the final successful smoke.
2. Record target public identity without printing DSN secret contents:
   - host alias `api.gradievo.com`;
   - container `novaic-queue-staging-postgres`;
   - DSN file path only;
   - Queue Service loopback URL only.
3. Tie the counts to the successful smoke report run id.
4. Store a compact JSON count report under ledger artifacts.

## Acceptance Criteria

- Queue table counts are recorded after the successful smoke.
- Target public info is recorded with secrets redacted.
- Counts cite `.complex-problems/L20260522-091929/artifacts/queue-api-smoke-report.json`.
- Query failures, if any, are recorded without secret exposure.

## Verification Plan

- Use `docker exec novaic-queue-staging-postgres psql ...` from api host.
- Query `config.version`, table counts, and selected status histograms.
- Copy the redacted JSON report into ledger artifacts.

## Risks

- Staging rows may include prior failed attempts; record counts as observed rather than pretending exact per-run deltas.

## Assumptions

- The final successful smoke run id is `20260522T165950Z-74bc8a64`.
