# Check: Cortex Archive Diagnostics Persistence Source Map

## Summary

Success. R355 solves P375: it identifies the exact Cortex persistence helper, the semantic remaining-stack computation, the writer payload shape, and the projection consumer that requires the top-level `remaining_stack` to remain a list.

## Evidence

- R355 cites `novaic-cortex/novaic_cortex/api.py:447-468`, `479-495`, and `656-744`.
- R355 cites `novaic-cortex/novaic_cortex/context_event_writer.py:74-90`.
- R355 cites `novaic-cortex/novaic_cortex/context_event_projection.py:113-119`.

## Criteria Map

- Identify code that builds `WakeArchived`: satisfied by `_append_wake_archived_event(...)` and `ContextEventWriter.wake_archived(...)`.
- Identify semantic active-stack `remaining_stack`: satisfied by `_semantic_remaining_stack_after_archive(...)` and projection consumer notes.
- Identify safest diagnostic shape: satisfied by nested `archive_diagnostics`.
- Identify focused tests: satisfied by suggested diagnostic scope_end test plus unchanged structural tests.

## Execution Map

Read-only source inspection only. No production code changed for P375.

## Stress Test

The key ambiguity was the duplicate name `remaining_stack`. R355 explicitly separates the semantic top-level list from the runtime diagnostic dict and warns not to replace the existing field.

## Residual Risk

Implementation remains in P376.

## Result IDs

- R355
