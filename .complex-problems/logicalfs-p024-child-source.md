# Delete Old Cortex Authority Source

## Problem

`novaic-cortex/novaic_cortex/workspace_files.py` still contains `CortexLogicalFileAuthority`, and nearby source/docs in `store.py` still describe the old in-process authority. Even if not imported by active runtime, this production source residue can be revived by future edits.

## Success Criteria

- `workspace_files.py` is deleted or replaced with a non-production/test-only alternative.
- Production source has no `CortexLogicalFileAuthority` or `BlobCortexStore` definitions/imports.
- `store.py` wording no longer claims it is below `CortexLogicalFileAuthority`.
- Source-level residue scan passes for old authority names outside explicitly historical docs/tests.
