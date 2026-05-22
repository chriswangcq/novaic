# Verify Queue Workers And Outbox On Postgres Staging

## Problem Definition

Queue Service API smokes have proven HTTP endpoints and Postgres writes, but they do not prove representative worker processes and outbox workers can operate in the same Postgres staging runtime. The remaining risk is that workers still assume a local sqlite queue path, fail to start against the Queue Service URL, or leave outbox rows undrained.

## Proposed Solution

Use the existing api host staging deployment as the verification target. Start bounded task-worker and saga-worker processes against the staging Queue Service URL with Postgres queue environment variables. Then run the session and saga outbox worker paths, or a documented safe drain equivalent if a long-running worker loop is not appropriate for staging. Capture before/after Postgres counts, worker logs, exit behavior, and filesystem checks for sqlite queue residue.

## Acceptance Criteria

- A representative task worker starts against `http://127.0.0.1:19987` and exits only because of the bounded smoke timeout or a controlled idle path.
- A representative saga worker or safe saga worker equivalent starts against the same staging Queue Service target.
- Session and saga outbox worker paths, or documented safe drain equivalents, run with `NOVAIC_QUEUE_DB_BACKEND=postgres` and the staging DSN file.
- Before/after Postgres counts and relevant outbox/task/saga/session outcomes are saved as an artifact.
- The staging runtime is checked for new `queue.db` or sqlite queue holders, with any residue explicitly recorded.
- Any discovered Postgres worker bug is fixed, tested locally, redeployed to staging, and rerun before success is claimed.

## Verification Plan

Inspect the worker entrypoints and required flags, run the bounded worker commands on api with log capture, query the staging Postgres counts before and after, inspect the staging data directory for sqlite files before and after, and save a JSON or Markdown report under the ledger artifacts directory. Treat timeout from an intentionally bounded idle worker as acceptable only when logs show startup without stack traces.

## Risks

- A task worker may need a live business or cortex endpoint for non-idle work; if so, keep the task-worker check to startup/connectivity and avoid staging-unsafe payload execution.
- Outbox drains may create additional saga/session rows; record the exact count deltas and keep the operation on the isolated staging Postgres container.
- Worker loops may run forever by design; use bounded timeouts and inspect logs rather than expecting natural process exit.

## Assumptions

- The api host staging Queue Service at `127.0.0.1:19987` remains the active test target.
- The staging Postgres DSN is supplied by `/opt/novaic/queue-staging-postgres/queue-postgres.dsn` and should not be printed into artifacts.
- It is acceptable to use the isolated staging Postgres container for safe smoke rows and outbox drains.
