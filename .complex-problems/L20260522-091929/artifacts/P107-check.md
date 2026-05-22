# P107 Success Check

## Summary

Success. Result `R115` solves the original worker/outbox Postgres staging smoke problem. The first failed run exposed real worker-path defects, but the final rerun after fixes proved task, saga, session outbox, and saga outbox worker paths against the api staging Postgres target with no sqlite residue.

## Evidence

- `R115` records the final smoke run `20260522T172306Z` with `ok=true`.
- `.complex-problems/L20260522-091929/artifacts/queue-worker-postgres-smoke-report.json` contains the captured worker process results, before/after DB counts, histograms, sqlite file scan, and `lsof` holder scan.
- Local regression tests passed: 72 focused tests covering Postgres queue boundaries, worker shutdown, outbox worker DB selection, placeholder conversion, and prior Queue Service Postgres mutation paths.
- The api staging Queue Service health endpoint returned `database_backend=postgres` after redeploy and restart.

## Criteria Map

- Representative task worker starts against staging Queue Service: satisfied by `task-worker` in the report, with startup line present, Queue Service URL `http://127.0.0.1:19987`, clean bounded shutdown, return code `0`, no traceback, and no error marker.
- Saga worker or safe saga worker equivalent starts: satisfied by `saga-worker` in the report, with registered saga definitions, startup line present, clean bounded shutdown, return code `0`, no traceback, and no error marker.
- Session/saga outbox worker or safe drain equivalent runs: satisfied by `session-outbox-worker` and `saga-outbox-worker`, both started in Postgres mode and shut down cleanly. Session outbox drained two pending rows to published; saga outbox ran against an empty outbox without errors.
- No new sqlite `queue.db` holder: satisfied by empty before/after sqlite file scans under `/opt/novaic/queue-service-staging` and `lsof +D /opt/novaic/queue-service-staging/data` showing no `queue.db` or sqlite matches.
- Worker/outbox outcomes and DB counts recorded: satisfied by the JSON artifact, including count deltas and histograms before and after the run.

## Execution Map

- Initial smoke found: direct sqlite construction in outbox worker assemblies, shutdown method shadowing, and Postgres placeholder conversion failure around `LIMIT ? FOR UPDATE SKIP LOCKED`.
- Fixes were implemented and tested locally before redeployment.
- Staging was updated and Queue Service was restarted with Postgres backend.
- Final smoke launched the four worker commands with bounded time windows and captured logs/DB state.
- Final DB outcome: `tq_session_outbox` moved from `pending=2` to `published=2`; saga rows increased from `2` to `4`; saga events increased from `7` to `10`; no sqlite files appeared.

## Stress Test

The check covered a plausible migration failure mode: worker processes that are not part of HTTP API smokes still attempted direct sqlite access and had signal-shutdown/runtime SQL issues. The final rerun proved those worker paths now use the Postgres boundary and survive controlled shutdown without stack traces.

## Residual Risk

Residual risk is non-blocking: the smoke uses bounded idle or low-impact drains rather than a full production business workload. That is appropriate for this staging criterion because the original problem required representative worker startup, outbox drain behavior, Postgres mode DB counts, and sqlite residue checks, all of which are evidenced.

## Result IDs

- R115
