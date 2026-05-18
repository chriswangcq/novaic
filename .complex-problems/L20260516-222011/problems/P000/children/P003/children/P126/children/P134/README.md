# Workspace materialized projections and payload reference map

## Problem

Workspace files such as `context.jsonl`, `steps/*.json`, `_index.jsonl`, and `payloads/*.json` are materialized observability and retrieval surfaces. Their authority relative to ContextEvents and LLM context must be verified.

## Success Criteria

- `workspace.py` context append, step write, index write, and payload write/read functions are mapped.
- Tool step write behavior is verified to require payload/payload_ref rather than inline raw result.
- `context.jsonl` and context projection write paths are classified as active source, debug projection, compatibility, or stale.
- Tests covering payload externalization, step indexes, and context writes are identified and run.
- Any stale or misleading materialized projection path is removed or split for cleanup.
