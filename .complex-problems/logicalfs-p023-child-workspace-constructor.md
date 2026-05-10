# Refactor Workspace To Depend On LogicalFS Authority

## Problem

`Workspace.__init__` still accepts a direct `CortexStore` and constructs `CortexLogicalFileAuthority`. This keeps live file authority inside Cortex. This belongs under P023 because Workspace is the central active dependency boundary.

## Success Criteria

- `Workspace.__init__` accepts a LogicalFS authority/port, not `CortexStore`.
- `workspace.py` no longer imports `CortexStore`, `CortexLogicalFileAuthority`, or `logical_to_store_key`.
- Directory listing maps LogicalFS directory entries to Cortex `FileEntry` without leaking store keys.
- Workspace initialization writes default layout through the authority explicitly.
- Targeted Workspace tests pass through the new constructor/helper.
