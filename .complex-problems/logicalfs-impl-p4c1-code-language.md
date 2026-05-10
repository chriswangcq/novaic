# Clean Stale Blob Language In Code Comments

## Problem

Code docstrings and comments still imply that Workspace/Store production semantics are Blob-backed. These comments sit near active constructors and are likely to mislead future code changes.

This child belongs under T010 because code-adjacent language should be cleaned before broader docs.

## Success Criteria

- `WorkspaceRegistry` comments/docstrings no longer describe live Workspace as Blob-backed authority.
- `CortexStore` / `LocalFileStore` comments no longer claim production live Workspace uses `BlobCortexStore` as the semantic authority.
- Workspace authority comments consistently point to LogicalFS/Cortex file authority for live `RO` / `RW`.
- Transitional adapter comments remain precise and local to `blob_store.py` / registry construction.
