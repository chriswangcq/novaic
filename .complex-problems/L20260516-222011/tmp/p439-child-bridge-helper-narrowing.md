# Runtime bridge materialized context helper narrowing

## Problem

`CortexBridge.read_context`, `append_context`, and `append_context_batch` are broad names that can be mistaken for authoritative LLM history APIs. They should be narrowed or renamed to materialized projection terminology if they remain.

## Success Criteria

- Runtime bridge helper names make their projection-only role explicit.
- Runtime callers are updated to the new names.
- No LLM prepare path calls the projection helpers.
- Focused runtime tests pass.

