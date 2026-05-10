# Migrate Cortex to common sandbox infrastructure

## Problem

Cortex should consume the common primitives and keep only Cortex-specific LogicalFS/Workspace/shell capability semantics.

## Success Criteria

- `novaic-cortex` imports process/mount/filesystem primitives from `common.sandbox`.
- Duplicate generic implementations are removed from Cortex.
- Cortex full tests pass.
