# Workspace context.jsonl projection map

## Problem

`context.jsonl` helpers still append and read materialized message projections. Their role must be classified precisely so they do not get mistaken for the authoritative LLM context source.

## Success Criteria

- `read_context`, `append_context`, `append_context_projection`, `append_context_batch`, and `append_context_batch_projection` are mapped with source pointers.
- Consumers/callers of these helpers are identified.
- The helpers are classified as materialized/debug projection, compatibility path, active source, or stale.
- If any active LLM prepare path reads `context.jsonl` as authority, it is fixed or split.
- Tests covering context write projections are identified and run.
