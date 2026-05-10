# Remove runtime lifecycle methods

## Problem

`novaic_cortex.runtime.Cortex` still defines `scope_create` and `scope_end`, so runtime callers can create or archive scope files directly through Workspace without emitting ContextEvents. This is a bypass even if active production code no longer uses it.

## Success Criteria

- `Cortex.scope_create` and `Cortex.scope_end` are physically removed from `novaic_cortex/runtime.py`.
- Runtime façade documentation/comments no longer advertise internal scope lifecycle management.
- A guard test asserts the runtime façade does not expose these methods.
- Focused runtime import/guard tests pass.
