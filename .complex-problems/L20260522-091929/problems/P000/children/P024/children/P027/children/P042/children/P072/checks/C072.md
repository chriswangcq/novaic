# Restart Business Services After Entangled Postgres Cutover Check

## Summary

P072 is successful. Result `R069` restarted Business API and Business subscriber after the Entangled Postgres cutover, verified Business health/subscriber metrics, and confirmed Entangled stayed ready without recreating SQLite files.

## Evidence

- Business API process PID `3569203` is running with `--entangled-url http://127.0.0.1:19900`.
- Business subscriber process PID `3569211` is running with `--entangled-url http://127.0.0.1:19900`.
- Business `/health` returned HTTP 200 with `status: healthy`.
- Subscriber metrics returned HTTP 200.
- Entangled `/v1/ready` returned HTTP 200 with 22 entities.
- Active-path `entangled.db*` files are absent.
- Restart report records `sqlite_holders_count: 0`.
- Restart report records no raw DSN/token/JWT values.
- Business log tail contained only a benign INFO schema-push line with `errors: none`; subscriber error tail was empty.

## Criteria Map

- Business API running on production loopback port: satisfied.
- Business health/readiness or representative endpoint passes: satisfied by `/health` HTTP 200.
- Business subscriber running: satisfied.
- Both use Entangled URL 19900: satisfied by process args.
- Entangled remains ready with 22 entities: satisfied.
- `entangled.db*` remains absent/unheld: satisfied.
- No schema/raw-secret log errors: satisfied by restart report.
- Redacted restart verification report recorded: satisfied.

## Execution Map

- T071 executed the restart as one bounded attempt.
- R069 recorded process, endpoint, Entangled, SQLite absence, and secret-policy evidence.
- No runtime child problem was needed.

## Stress Test

- Business startup re-pushed schemas against Entangled; Entangled remained ready and did not emit schema errors.
- Subscriber metrics showed internal requests targeting `127.0.0.1:19900`, proving it is exercising the PG-mode Entangled endpoint.

## Residual Risk

- No known blocker remains for Business restoration in the Entangled cutover scope.

## Result IDs

- R069
