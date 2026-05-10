# Cut Cortex live RO/RW operations behind LogicalFS

## Problem

Cortex owns scope/workspace semantics, but live file operations for shell
`RO` / `RW` must be owned by LogicalFS. Any direct live Workspace persistence
or shell file operation that bypasses LogicalFS must be migrated or explicitly
removed if obsolete.

## Success Criteria

- Cortex shell execution uses LogicalFS for materialization, stable paths, and
  patch observation/application.
- Workspace file operations that participate in live `RO` / `RW` are routed
  through LogicalFS or clearly isolated as non-live migration/storage internals.
- Tests prove shell output sanitization and file update persistence still work.
- No local fallback path silently executes shell without sandboxd/LogicalFS.
