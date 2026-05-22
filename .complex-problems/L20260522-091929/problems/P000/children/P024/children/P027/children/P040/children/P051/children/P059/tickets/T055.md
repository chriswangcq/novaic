# Run Entangled Postgres REST Smoke Suite And Report

## Problem Definition

The Postgres-mode Entangled staging runtime is ready. Run representative REST smokes against it using the staging service token file without exposing secrets, then write a redacted report and stop the staging process unless it must remain running.

## Proposed Solution

1. Use the running staging endpoint on `127.0.0.1:19910` and read the service token only inside the remote shell.
2. Verify health/readiness and schema availability.
3. Run REST operations against `rest-smoke-events`:
   - list/read existing fixture row,
   - upsert/read a singleton-style row,
   - append/query stream-style row,
   - patch update,
   - CAS update,
   - delete and confirm cleanup.
4. Capture non-secret endpoint statuses, IDs/counts, mutation cleanup evidence, and log tail.
5. Stop the staging process after smokes and verify the port is no longer listening.
6. Write the report under ledger artifacts.

## Acceptance Criteria

- REST smoke covers health/readiness, schema proof, list/read, upsert/read, append/query, update, delete, and CAS or equivalent rowcount-sensitive behavior.
- Auth uses the service-token file without printing token values.
- Smoke report contains endpoint statuses, entity name, row IDs/counts, and cleanup evidence.
- Report contains no DSNs, tokens, cookies, or env-file contents.
- Staging process is stopped or explicitly documented as intentionally left running.

## Verification Plan

Run the remote smoke script, inspect the redacted JSON report, check the staging log tail for errors, verify process cleanup, and record the result.

## Risks

- Entity schema shape may not support every operation cleanly; if a route fails, record exact HTTP status/body without secrets.
- Stopping the staging process too early would break later WebSocket validation, but `P052` is separate and can start its own process.

## Assumptions

- `P058` left the staging process running and registered `rest-smoke-events`.
