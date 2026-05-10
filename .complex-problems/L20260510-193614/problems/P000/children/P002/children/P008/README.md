# Phase 1B Cortex Service Boundary Wiring

## Problem

Wire the operational SQLite store through Cortex construction boundaries so the substrate is on the live service path, without making it the authority for old behavior before Phase 2 and Phase 3 migrations.

## Success Criteria

- Cortex CLI/startup requires an operational SQLite filesystem path.
- `WorkspaceRegistry` receives an initialized operational store through explicit constructor/factory arguments.
- `Workspace` instances expose the same operational store port for later migration phases.
- Startup scripts pass a durable data-dir SQLite path.
- Existing dependency-boundary tests are updated to prove the store is explicit at the registry boundary.
