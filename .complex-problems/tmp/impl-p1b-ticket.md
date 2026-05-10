# Wire Operational Store Through Cortex Service Boundary

## Problem Definition

The operational SQLite store exists after Phase 1A, but it must be explicitly present on the Cortex live construction path. Otherwise the project repeats the historical failure mode where new code exists but production still uses old branches.

## Proposed Solution

Wire the store at the service boundary only:

- Add an explicit operational SQLite path argument to Cortex service startup.
- Build and initialize `OperationalSqliteStore` in the registry factory.
- Require `WorkspaceRegistry` to receive the initialized store explicitly.
- Pass the store into each `Workspace` instance as a stable port for later migration phases.
- Update startup scripts, dependency-boundary tests, and docs to expose the new dependency.

## Acceptance Criteria

- `main_cortex.py` requires `--operational-sqlite-path`.
- Startup scripts pass a durable `$DATA_DIR/cortex/operational.sqlite3` path.
- `WorkspaceRegistry` constructor cannot be created without an operational store.
- `Workspace` exposes `operational_store` from registry-built workspaces.
- Existing dependency-boundary tests are updated and pass.

## Verification Plan

- Run registry dependency-boundary tests.
- Run operational store tests again after wiring changes.
- Search service startup/docs for `operational-sqlite-path`.
- Search registry/workspace code to confirm no implicit memory fallback.

## Risks

- Making the argument optional would hide the dependency and weaken the boundary.
- Accidentally using the store as authority in this phase would blur with Phase 2/3.

## Assumptions

- The existing `scope_state_log_path` remains until Phase 2 migration.
- The operational store is initialized once per Cortex service process and shared through the registry.
