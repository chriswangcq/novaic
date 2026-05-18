# Persist Explicit Archive Diagnostics

## Problem

Implement explicit finalize diagnostics persistence in Cortex without conflating it with semantic remaining-stack lifecycle data.

## Success Criteria

- Diagnostic archive requests persist explicit `session_generation`, `finalize_reason`, diagnostic `remaining_stack`, and `round_num` in durable context-event metadata.
- Pure structural Cortex scope-end callers without diagnostics keep existing event payload shape.
- The implementation uses only `ScopeEndRequest` diagnostics for diagnostic metadata and does not synthesize generation from active state.
- Focused Cortex tests pass.

