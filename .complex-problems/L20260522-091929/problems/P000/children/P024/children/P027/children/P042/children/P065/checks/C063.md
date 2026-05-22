# Restart Production Entangled In Postgres Mode Check

## Summary

P065 is not successful yet. Result `R061` proves the old SQLite runtime was stopped and a Postgres-mode Entangled process is running with file-based secrets, but the original problem requires both health and readiness to succeed after restart. Readiness is still HTTP 503 because schema registration failed, leaving the runtime with zero registered entities.

## Blocking Gaps

- The success criterion "Health/readiness return success after restart" is not met: `/v1/health` returned HTTP 200, but `/v1/ready` returned HTTP 503 `not_ready`.
- The PG runtime has `0` registered entities, so it is not serving the migrated production schema surface.
- Production log evidence points to a concrete code defect: literal `%` in Business schema DDL is not escaped before psycopg receives the converted SQL.
- Business API/subscriber remain frozen and cannot safely be restarted until Entangled readiness is repaired and verified.

## Result IDs

- R061
