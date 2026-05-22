# Queue Startup Default Cleanup Result

## Summary

Cleaned the remaining active Queue startup default that could implicitly select SQLite. `main_novaic.py` now defaults the Queue CLI wrapper to Postgres, and the focused startup-default guard test now covers both `queue_service/main.py` and `main_novaic.py`.

## Done

- Updated `novaic-agent-runtime/main_novaic.py` so `--db-backend` defaults from `NOVAIC_QUEUE_DB_BACKEND` with fallback `postgres` instead of `sqlite`.
- Preserved explicit SQLite selection via `choices=("sqlite", "postgres")`; SQLite remains opt-in rather than an accidental default.
- Updated `novaic-agent-runtime/tests/test_queue_runtime_postgres_default.py` with a guard for the CLI wrapper default.
- Checked for active-code occurrences of `NOVAIC_QUEUE_DB_BACKEND` defaulting to `sqlite`; remaining matches are only negative test assertions.

## Verification

- `python -m pytest tests/test_queue_runtime_postgres_default.py` from `novaic-agent-runtime` passed: 4 tests passed.
- Residue search:
  - `rg -n 'NOVAIC_QUEUE_DB_BACKEND.*sqlite|default=os\.environ\.get\("NOVAIC_QUEUE_DB_BACKEND", "sqlite"\)' novaic-agent-runtime -g '*.py'`
  - Result: only `tests/test_queue_runtime_postgres_default.py` negative assertions mention the old SQLite default string.

## Known Gaps

- Queue Service was not started because P110/R103 still has no confirmed non-production Queue Postgres DSN/DSN file.
- The `novaic-agent-runtime` sub-repository already contained many unrelated dirty files; this ticket only touched `main_novaic.py` and `tests/test_queue_runtime_postgres_default.py`.

## Artifacts

- `novaic-agent-runtime/main_novaic.py`
- `novaic-agent-runtime/tests/test_queue_runtime_postgres_default.py`
- `.complex-problems/L20260522-091929/artifacts/P114-T109-result.md`
