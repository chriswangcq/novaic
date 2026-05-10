# P000: Runtime ToolOutputV1 normalization

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Runtime tool execution still stores executor results as raw strings or JSON dictionaries in `content`. The shell/display architecture needs every durable tool result to converge on `ToolOutputV1` so Cortex can project bounded text plus artifact manifests instead of treating raw `_mcp_content` or multimodal fields as history truth.

## Success Criteria
- `task_queue.handlers.tool_handlers._ok()` stores successful executor output as `ToolOutputV1` JSON.
- Logical tool failure semantics are preserved: executor results with `success=false` or `ok=false` still produce `tool_success=false` and `tool_status=error`.
- Existing small text/dict tools remain readable through the `ToolOutputV1.text` field.
- Tests cover success, logical failure, and one mounted-device execution path under the new content envelope.
- Focused Runtime tool handler tests pass.

## Subproblems
- P001: Normalize Runtime tool error paths to ToolOutputV1

## Results
- R000

## Latest Check
C002

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R000: problems/P000/results/R000.md
- Check C000: problems/P000/checks/C000.md
- Check C002: problems/P000/checks/C002.md

## Follow-ups
- P001: Normalize Runtime tool error paths to ToolOutputV1
