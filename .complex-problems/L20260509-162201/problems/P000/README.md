# Runtime ToolOutputV1 normalization

## Problem

Runtime tool execution still stores executor results as raw strings or JSON dictionaries in `content`. The shell/display architecture needs every durable tool result to converge on `ToolOutputV1` so Cortex can project bounded text plus artifact manifests instead of treating raw `_mcp_content` or multimodal fields as history truth.

## Success Criteria

- `task_queue.handlers.tool_handlers._ok()` stores successful executor output as `ToolOutputV1` JSON.
- Logical tool failure semantics are preserved: executor results with `success=false` or `ok=false` still produce `tool_success=false` and `tool_status=error`.
- Existing small text/dict tools remain readable through the `ToolOutputV1.text` field.
- Tests cover success, logical failure, and one mounted-device execution path under the new content envelope.
- Focused Runtime tool handler tests pass.
