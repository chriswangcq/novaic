# Runtime step-ref display projection selection

## Problem

Audit runtime step-ref expansion so current `display` tool messages are resolved with `display_perception`, while non-display current tools use `current_tool_result` and historical tools use `history`.

## Success Criteria

- Map `_projection_for_tool_message`, tool-name lookup, latest-tool-call fallback, and Cortex formatted read calls.
- Prove current `display` gets `display_perception`.
- Prove historical `display` does not get `display_perception`.
- Prove current non-display tool messages do not get display media projection.

