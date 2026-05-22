# Repair Entangled Postgres Placeholder Escaping And Complete Production Readiness

## Problem Definition

Production Entangled is already running in Postgres mode on `127.0.0.1:19900`, but schema registration fails because the Postgres SQL adapter does not escape literal `%` characters before sending converted SQLite-style SQL to psycopg. The current runtime is healthy but not ready, with zero registered entities, and Business API/subscriber remain frozen.

## Proposed Solution

Patch `PostgresDatabase._convert_placeholders` so it still converts unquoted `?` parameter placeholders to `%s`, while also escaping every literal `%` as `%%` for psycopg. Add a regression test for DDL containing a literal `LIKE 'blob://%'` pattern and run focused Entangled tests locally.

After local validation, deploy the patched `database.py` to the API host, restart the PG-mode Entangled process using the existing file-backed DSN and service-token arguments, then push Business schemas and Device schemas directly to Entangled without starting Business writers. Verify health/readiness, entity count, process arguments, listener state, and absence of SQLite file holders.

## Acceptance Criteria

- `PostgresDatabase._convert_placeholders` escapes literal `%` characters for psycopg while preserving `?` to `%s` behavior outside SQL quotes.
- A focused regression test covers literal percent DDL.
- Focused local Entangled tests pass.
- The patched Entangled SQL adapter is deployed to the API host.
- The production Entangled process is restarted on `127.0.0.1:19900` in Postgres mode with `--postgres-dsn-file` and `--service-token-file`.
- Business and Device schema registration succeeds without unfreezing Business API/subscriber.
- `/v1/health` and `/v1/ready` return HTTP 200 with the expected schema/entity set.
- No live process holds `/opt/novaic/data/entangled.db*`.
- Process arguments contain no raw DSN or raw service-token values.
- A redacted runtime repair report is recorded in ledger artifacts.

## Verification Plan

Run targeted pytest coverage for the Postgres database boundary and existing schema/notifier/WebSocket smoke logic. On the API host, use sanitized process inspection, `ss`, `curl` health/readiness checks, direct schema push outputs, log tail review, and `lsof` against SQLite files. Keep DSN/token values out of command output and recorded artifacts.

## Risks

- Restarting the current PG-mode process before the fix is deployed would keep readiness broken.
- Direct Device schema registration must bypass Business proxy because Business remains frozen.
- If expected entity count differs from prior staging assumptions, verification must record the actual entity names/count and decide whether any missing schema is blocking.
- Printing remote process or script inputs carelessly could expose secrets.

## Assumptions

- The P064 Postgres migration data remains intact in `novaic_entangled`.
- The current file-backed production DSN and service-token files are present and readable by root.
- Business API/subscriber should remain stopped until later production smokes complete.
- The deployed Entangled code path on the API host is `/opt/novaic/services/Entangled/packages/server-python`.
