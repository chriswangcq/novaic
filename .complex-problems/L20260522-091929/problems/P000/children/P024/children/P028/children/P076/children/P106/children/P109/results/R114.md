# Queue API Staging Target And Smoke Closure Result

## Summary

`T106` split `P109` into target confirmation, Queue Service startup, API smokes, and post-smoke count reporting. All four child problems are now closed with evidence. The final state is a dedicated non-production Queue Postgres target on `api.gradievo.com`, a running Postgres-mode Queue Service, successful API smokes, and redacted post-smoke counts.

## Done

- Closed `P110: Confirm Non-Production Queue Postgres Target`.
  - Early result `R103` showed no safe target was available in the original local runner and correctly prevented writes.
  - Later child path provisioned the safe staging target under `P117/R107`.
- Closed `P111: Start Queue Service In Postgres Mode`.
  - Result `R111`, check `C125`.
  - Final running service: `http://127.0.0.1:19987`, backend Postgres, DSN file path only.
- Closed `P112: Run Queue Service API Smokes`.
  - Result `R112`, check `C126`.
  - Final smoke report `ok=true`, 26 operations, no skips.
- Closed `P113: Record Queue Postgres Post-Smoke Counts`.
  - Result `R113`, check `C127`.
  - Count report recorded target identity and table counts with secrets redacted.

## Verification

- Queue Service startup:
  - `/health` healthy.
  - `/ready` ok.
  - schema version `18`.
- API smoke report:
  - `.complex-problems/L20260522-091929/artifacts/queue-api-smoke-report.json`.
  - run id `20260522T165950Z-74bc8a64`.
  - task complete/fail, saga complete/fail, session dispatch/session-ended, and idempotency contention/completed replay all passed.
- Count report:
  - `.complex-problems/L20260522-091929/artifacts/queue-post-smoke-count-report.json`.
  - target `api.gradievo.com`, `novaic-queue-staging-postgres`, `127.0.0.1:15432`, database/user `novaic_queue_staging`, DSN secret redacted.
  - key counts include `tq_tasks=2`, `tq_sagas=2`, `tq_session_events=6`, `tq_idempotency_ledger=1`.
- Local focused regression tests for discovered Postgres runtime defects:
  - `49 passed in 0.14s`.

## Known Gaps

- The fixes discovered during staging must still be committed and pushed.
- The staging service is intentionally isolated and loopback-only; production cutover remains governed by higher-level ledger work.

## Artifacts

- `R111`, `C125`: Queue Service Postgres-mode startup.
- `R112`, `C126`: API smoke success.
- `R113`, `C127`: Post-smoke count report.
- `.complex-problems/L20260522-091929/artifacts/queue-api-smoke-report.json`.
- `.complex-problems/L20260522-091929/artifacts/queue-post-smoke-count-report.json`.
