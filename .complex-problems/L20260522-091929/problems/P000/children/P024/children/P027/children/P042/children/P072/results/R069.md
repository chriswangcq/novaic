# Restart Business Services After Entangled Postgres Cutover Result

## Summary

Restarted Business API and Business subscriber after the Entangled Postgres cutover. Business API is healthy on `127.0.0.1:19998`, Business subscriber is running with metrics available on `127.0.0.1:19985`, and both processes point at Entangled `http://127.0.0.1:19900`.

Entangled remained ready with 22 entities after the restart, and `/opt/novaic/data/entangled.db*` was not recreated or held.

## Done

- Started Business API with the production venv and `--entangled-url http://127.0.0.1:19900`.
- Started Business subscriber with the production venv and `--entangled-url http://127.0.0.1:19900`.
- Wrote Business logs under `/opt/novaic/data/logs`.
- Verified Business API health.
- Verified subscriber metrics endpoint.
- Verified Entangled readiness after Business restart.
- Verified no active Entangled SQLite files.
- Pulled the redacted restart verification report into local ledger artifacts.

## Verification

- Business API PID `3569203` is running.
- Business subscriber PID `3569211` is running.
- `curl http://127.0.0.1:19998/health` returned HTTP 200 with `status: healthy`.
- Subscriber metrics returned HTTP 200.
- Entangled `/v1/ready` returned HTTP 200 with 22 entities.
- `find /opt/novaic/data -maxdepth 1 -name 'entangled.db*'` returned no files.
- Restart report records `sqlite_holders_count: 0`.
- Restart report records `report_contains_secret: false`.
- Business log tail only included an INFO schema-push line with `errors: none`; subscriber error tail was empty.

## Known Gaps

- No remaining Business restart gap is known from this ticket.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/business-restart-after-entangled-cutover-report.json`
- `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z/business-restart-after-entangled-cutover-report.json`
