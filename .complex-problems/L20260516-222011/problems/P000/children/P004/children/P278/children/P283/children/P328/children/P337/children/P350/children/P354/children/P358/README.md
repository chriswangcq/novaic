# Subagent finalize status handler validation

## Problem

`handle_subagent_set_sleeping()` and `handle_subagent_set_completed()` can currently call `business_client.entity_update()` without validating wake/session identity. Missing or non-positive generation must be rejected before any Business mutation.

## Success Criteria

- Inspect `task_queue/handlers/subagent_handlers.py` terminal status handlers.
- Require `scope_id` and positive `session_generation` before `entity_update()`.
- Keep Business update schema minimal; do not write unknown audit fields unless code-backed evidence shows they are accepted.
- Add tests that missing `scope_id`, missing generation, zero generation, and malformed generation fail before Business mutation.
- Keep non-finalize subagent handlers unchanged unless a direct dependency is proven.
