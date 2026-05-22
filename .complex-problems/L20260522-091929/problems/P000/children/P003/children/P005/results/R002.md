# T004 Result: LLM Factory Has an Explicit Postgres Backend Path

## Summary

Added an explicit Postgres backend path to `novaic-llm-factory` while preserving SQLite as the default/rollback backend. The existing `FactoryDB` API remains the route-facing interface, so the FastAPI routes do not need broad rewrites.

Production runtime was not cut over in this ticket.

## Done

- Updated `factory/db.py` with:
  - Postgres schema creation for `api_keys`, `models`, `user_keys`, and `llm_logs`.
  - A small psycopg-backed connection/cursor wrapper that preserves the existing row/dict access shape used by the service.
  - SQL translation for existing `?` placeholders, `datetime('now')`, and the one SQLite `INSERT OR IGNORE` path.
  - Backend selection in `FactoryDB(..., backend="postgres", dsn=...)`.
- Updated `factory/config.py` with:
  - `database.backend`
  - `database.dsn`
  - `database.dsn_file`
  - `LLM_FACTORY_DATABASE_DSN`
  - `LLM_FACTORY_DATABASE_DSN_FILE`
- Updated `factory/app.py` to pass backend/DSN config into `FactoryDB`.
- Updated `config.example.json` to keep the default backend explicit as SQLite.
- Added `psycopg[binary]>=3.1.0` to `requirements.txt`.

## Verification

- `python3 -m compileall factory`: passed.
- `python3 -m pytest tests/test_log_routes.py`: 6 passed.
- `python3 -m pytest`: 19 passed.
- `git diff --check -- factory/config.py factory/app.py factory/db.py config.example.json requirements.txt`: passed.
- Postgres smoke via SSH tunnel to `api` local Postgres passed:
  - Created schema in `novaic_llm_factory`.
  - Inserted/read/deleted an API key, model, and log using the Postgres backend.
  - Re-ran with full requirements installed and verified encrypted API key storage/decryption.
  - Confirmed smoke rows were cleaned up afterward: `0|0|0` for smoke `api_keys|user_keys|llm_logs`.

## Known Gaps

- The deployed `novaic-llm-factory` Docker container has not been rebuilt or restarted with this code yet.
- Existing SQLite production rows have not been migrated yet.
- The Postgres schema now exists in `novaic_llm_factory` because the smoke initialized it, but production data cutover remains pending.

## Artifacts

- Modified source files:
  - `novaic-llm-factory/factory/db.py`
  - `novaic-llm-factory/factory/config.py`
  - `novaic-llm-factory/factory/app.py`
  - `novaic-llm-factory/config.example.json`
  - `novaic-llm-factory/requirements.txt`
- Postgres smoke target: `novaic_llm_factory` database on `api.gradievo.com`.
