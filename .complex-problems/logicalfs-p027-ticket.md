# Refactor Runtime And Registry Wiring

## Problem Definition

After Workspace constructor cutover, active runtime and registry wiring must pass LogicalFS authorities into Workspace. `Cortex.__init__` must stop exposing the old `store, agent_id` live constructor path.

## Proposed Solution

Update `WorkspaceRegistry` to call `build_workspace_file_authority` for each `(user, agent)` workspace. Update `Cortex.__init__` to require an explicit `workspace` and remove direct store construction parameters. Keep API `_build_cortex(ws)` workspace-based. Run targeted import/source scans and minimal runtime construction tests.

## Acceptance Criteria

- `WorkspaceRegistry` constructs `Workspace(authority, agent_id, ...)`.
- `Cortex.__init__` no longer accepts `store` / `agent_id` as a Workspace construction path.
- `runtime.py` no longer imports `CortexStore`.
- `api.py` remains workspace-based.
- Source scans show no direct store construction in runtime/registry active paths.

## Verification Plan

- Update runtime and registry source.
- Run targeted tests that can pass before full test migration.
- Run scans for old constructor/store imports in runtime/registry/API.

## Risks

- Many tests will fail until P028 migrates them to explicit helpers.
- Any retained compatibility branch in runtime would undermine the boundary.

## Assumptions

- API server already obtains a `Workspace` from registry and passes it to `Cortex(workspace=ws)`.
