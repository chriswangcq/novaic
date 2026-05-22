# P114 Success Check

## Summary

P114 is successful. R104 removed the misleading Queue CLI wrapper SQLite default, preserved explicit SQLite opt-in, and added focused regression coverage for both Queue startup entrypoints.

## Evidence

- `novaic-agent-runtime/main_novaic.py` now uses `default=os.environ.get("NOVAIC_QUEUE_DB_BACKEND", "postgres")` for `--db-backend`.
- `choices=("sqlite", "postgres")` remains, so SQLite is still explicit rather than deleted from adapter/test use.
- `novaic-agent-runtime/tests/test_queue_runtime_postgres_default.py` now guards the CLI wrapper default in addition to `queue_service/main.py`.
- Focused pytest passed: `python -m pytest tests/test_queue_runtime_postgres_default.py` produced 4 passing tests.
- Residue search found the old SQLite default string only in negative test assertions.

## Criteria Map

- Active Queue Service startup entrypoints default `NOVAIC_QUEUE_DB_BACKEND` to `postgres`: satisfied for `queue_service/main.py` and `main_novaic.py`.
- SQLite remains available only through explicit selection for tests/adapter use: satisfied by keeping `choices=("sqlite", "postgres")` while removing implicit SQLite fallback.
- Focused tests guard the default and prevent regression: satisfied by the updated startup-default test file.
- The change is small and does not rewrite unrelated startup behavior: satisfied; only the default and focused guard were changed in this ticket.

## Execution Map

- Inspected the startup CLI residue.
- Patched the stale default.
- Added focused source guard coverage.
- Ran the focused default test file.

## Stress Test

- Plausible failure mode: a future edit reintroduces `sqlite` as the fallback. The new test checks that exact string is absent in both active startup surfaces.
- Plausible failure mode: the cleanup removes explicit SQLite support required for adapter tests. The `choices=("sqlite", "postgres")` assertion verifies explicit selection remains present.
- Plausible failure mode: only `queue_service/main.py` is guarded and wrapper drift returns. The test now checks `main_novaic.py` too.

## Residual Risk

- P111's actual service startup remains blocked on a missing non-production DSN, but that is outside P114's code-cleanup success criteria.
- The sub-repository remains broadly dirty from earlier unrelated work; this check only judges the P114 touched files.

## Result IDs

- R104
