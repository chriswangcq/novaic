# P027 Runtime Registry Wiring Check

## Summary

Success for P027. Active registry wiring now constructs a LogicalFS authority and passes it to Workspace, and `Cortex.__init__` no longer offers the old direct store/agent constructor.

## Evidence

- `registry.py` imports `BlobObjectStore` from `logicalfs` and `build_workspace_file_authority` from Cortex's semantic factory.
- `registry.py` builds `authority = build_workspace_file_authority(object_store, agent_id)` and calls `Workspace(authority, agent_id, ...)`.
- `runtime.py` requires `workspace: Workspace` and no longer imports `CortexStore` or accepts `store` / `agent_id`.
- API `_build_cortex(ws)` still calls `Cortex(workspace=ws, ...)`.
- Runtime smoke construction succeeded with an explicit Workspace.
- Source scan found no relevant old runtime/registry/API active-path hits.

## Criteria Map

- Registry constructs Workspace from LogicalFS authority: satisfied.
- Runtime no longer exposes store/agent constructor path: satisfied.
- API remains workspace-based: satisfied.
- Runtime/registry active scans clean: satisfied.

## Execution Map

- Patched registry active Workspace construction.
- Patched runtime constructor signature and removed obsolete imports/parameters.
- Ran a runtime construction smoke and source scans.

## Stress Test

- Checked that the scan included runtime, registry, and API together so a fallback could not hide in adjacent active wiring.
- Removed unused runtime collaborator parameters instead of leaving a misleading compatibility surface.

## Residual Risk

- Full test suite is not expected to pass until P028 migrates tests away from old direct constructors.
- Store modules and old authority source still exist until P024 cleanup.

## Result IDs

- R024
