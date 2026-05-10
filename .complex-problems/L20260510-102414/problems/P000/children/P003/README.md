# Make LogicalFS storage dependency explicit

## Problem

LogicalFS currently reaches into `Workspace._store` and `_key`, which works but hides the intended boundary: LogicalFS should depend on a workspace/storage port, while Blob/store remains the lower byte-object substrate.

## Success Criteria

- LogicalFS uses a public workspace-facing method or small explicit port for listing materialized paths.
- Private workspace internals are not the normal LogicalFS dependency.
- Tests still prove `/ro` materialization and `/rw` flush semantics.
