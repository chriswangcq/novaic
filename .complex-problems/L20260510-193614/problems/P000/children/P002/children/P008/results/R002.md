# Phase 1B Result

## Summary

Wired the operational SQLite store through Cortex service construction boundaries without migrating old behavior yet.

## Done

- Updated `WorkspaceRegistry` to require an explicit `operational_store` constructor dependency.
- Updated `build_workspace_registry` to require `operational_sqlite_path`, initialize `OperationalSqliteStore`, and pass an explicit runtime clock/id provider at the boundary.
- Updated `Workspace` to carry and expose the operational store port.
- Updated `main_cortex.py` to require `--operational-sqlite-path` and pass it into registry construction.
- Updated `scripts/start.sh` to provide `$DATA_DIR/cortex/operational.sqlite3`.
- Updated `docs/cortex/deployment-and-startup.md` to document `--sandboxd-url` and `--operational-sqlite-path`.
- Updated registry dependency-boundary tests to assert the constructor dependency is explicit and registry-built workspaces expose the same store.

## Verification

- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_operational_store.py novaic-cortex/tests/test_workspace_registry_dependencies.py`
  - Result: `9 passed in 0.13s`
- `python3 -m py_compile novaic-cortex/novaic_cortex/main_cortex.py novaic-cortex/novaic_cortex/registry.py novaic-cortex/novaic_cortex/workspace.py novaic-cortex/novaic_cortex/operational_store.py`
  - Result: passed.
- `rg -n "operational-sqlite-path|operational_sqlite_path" ...`
  - Result: startup script, docs, CLI parser, and registry factory all reference the new path.
- `rg -n "build_workspace_registry\\(" novaic-cortex docs scripts`
  - Result: only main Cortex, registry definition, and the updated test call the factory.

## Known Gaps

- `python -m novaic_cortex.main_cortex --help` could not run in this local shell because `uvicorn` is not installed in the current interpreter. This was mitigated with `py_compile` and targeted tests. Runtime startup uses the service venv in deployment.
- The operational store is wired but not yet authoritative for scope transition logs or active stack/status; those are intentionally owned by Phase 2 and Phase 3.

## Artifacts

- `novaic-cortex/novaic_cortex/registry.py`
- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-cortex/novaic_cortex/main_cortex.py`
- `scripts/start.sh`
- `docs/cortex/deployment-and-startup.md`
- `novaic-cortex/tests/test_workspace_registry_dependencies.py`
