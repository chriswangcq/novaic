# Normalize Runtime tool error paths to ToolOutputV1

## Problem

Runtime `_ok()` now normalizes successful executor returns to `ToolOutputV1`, but `_err()` still stores raw legacy JSON for unknown tool names and handler exceptions. This leaves one durable tool-result path outside the new contract.

## Success Criteria

- `_err()` stores `content` as `ToolOutputV1` JSON with `ok=false`.
- Unknown-tool and exception paths preserve current task status/error semantics.
- Tests assert the failure-path envelope has `version == "tool-output.v1"` and includes the error text.
- Focused Runtime tool handler failure tests pass.
