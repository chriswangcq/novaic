# Cut Cortex Workspace Runtime To LogicalFS Authority

## Problem

Cortex must become a semantic client of LogicalFS instead of owning the live file persistence adapter. Workspace, runtime, API, and registry need to use the new LogicalFS authority in the active path. This belongs under T019 because defining a new authority is insufficient unless the live agent runtime is cut over to it.

## Success Criteria

- `Workspace` accepts or constructs only a LogicalFS authority/port for live file operations, not `CortexStore` or Blob persistence.
- Runtime/API/registry active construction paths pass explicit semantic owner/layout inputs into LogicalFS.
- Shell/sandbox RO/RW behavior still works through the cutover path.
- Existing tests are updated to use explicit LogicalFS test authorities or helpers rather than active direct store construction.
- Residue scans show no active `ws._store` or direct store access in Workspace/runtime/API.
