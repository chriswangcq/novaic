# Entangled WebSocket Smoke Client Result

## Summary

`T058` built a reproducible Entangled WebSocket smoke client and verified it locally plus against the Postgres-mode staging runtime from `P060`. The client authenticates with an Authorization-header JWT, reads secrets from files, records frame summaries/counts/order evidence, can trigger a REST append to observe a WebSocket delta, supports reconnect checks, and writes a JSON report that checks for raw secret leakage.

## Done

- Added `entangled.tools.ws_smoke` with CLI entry point `entangled-ws-smoke`.
- Added support for:
  - token/JWT secret/service token files.
  - Authorization-header JWT WebSocket auth.
  - schema/list/stream entangle frame summaries.
  - optional REST append to trigger delta frames.
  - controlled reconnect validation.
  - optional Postgres sync-version and stream `entangled_rowid` evidence.
  - report secret scanning.
  - `--skip-list` for staging schemas whose list rows contain non-JSON-safe fields.
- Added local unit tests for parameter parsing, frame summarization, stream-order redaction, secret detection, and SQL identifier guarding.
- Synced the smoke client to the API staging Entangled package.
- Ran a safe remote dry run against `ws://127.0.0.1:19910/v1/sync`.

## Verification

- Local targeted tests: `python -m pytest tests/test_ws_smoke_client.py` -> 6 passed.
- Local compile check: `python -m py_compile entangled/tools/ws_smoke.py` -> passed.
- Local full Entangled suite: `python -m pytest` -> 131 passed.
- Remote dry-run summary:
  - `schema_seen`: true.
  - `stream_sync_mode`: `head_n`.
  - `delta_seen`: true.
  - `reconnect_sync_mode`: `up_to_date`.
  - `query_string_token_used`: false.
  - `report_contains_secret`: false.
  - staging stream count advanced to 3 and max `entangled_rowid` advanced to 3.

## Known Gaps

- The remote dry run used `--skip-list` because a direct list entangle of `rest-smoke-events` exposed a server-side serialization issue: rows containing `blob_data` bytes cannot be sent with `send_json`. This is useful evidence for `P062`, which must either use a non-BLOB list fixture or fix/verify BLOB-safe serialization before claiming full list coverage.
- This ticket builds and minimally verifies the client. `P062` still owns the final WebSocket smoke report, full criteria mapping, and staging process cleanup.

## Artifacts

- `Entangled/packages/server-python/entangled/tools/ws_smoke.py`
- `Entangled/packages/server-python/entangled/tools/__init__.py`
- `Entangled/packages/server-python/tests/test_ws_smoke_client.py`
- `Entangled/packages/server-python/pyproject.toml`
- `.complex-problems/L20260522-091929/artifacts/entangled-ws-smoke-client-dryrun-summary.json`
- `/opt/novaic/logs/entangled-ws-smoke-client-dryrun.json`
