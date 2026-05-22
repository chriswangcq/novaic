# Queue Postgres Post-Smoke Counts Success Check

## Summary

`P113` is successful. `R113` records post-smoke Queue Postgres counts, status histograms, target public identity, and ties the evidence to the successful API smoke run without exposing secrets.

## Evidence

- Count report: `.complex-problems/L20260522-091929/artifacts/queue-post-smoke-count-report.json`.
- Smoke report: `.complex-problems/L20260522-091929/artifacts/queue-api-smoke-report.json`.
- Count report cites smoke run id `20260522T165950Z-74bc8a64`.
- Target public info records DSN file path only and marks DSN secret `redacted`.
- Container health is `healthy`.

## Criteria Map

- Post-smoke counts recorded for Queue migration tables: satisfied by 16 count keys including task, saga, worker lease, idempotency, and session tables.
- Target public info recorded with secrets redacted: satisfied by `target_public_info`.
- Counts tied to smoke run artifact: satisfied by `smoke_report` and `smoke_run_id`.
- Count query failure recorded if any: no failure occurred; report generation returned `ok=true`.

## Execution Map

- `R113` generated and summarized the redacted count report.

## Stress Test

- Counts were queried directly from the staging Postgres container after the successful smoke, not inferred from HTTP responses alone.

## Residual Risk

- Counts are staging evidence and include smoke rows; they are not a production baseline.

## Result IDs

- `R113`
