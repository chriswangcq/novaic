# Add stable running reasoning activity projection updates

## Problem

Runtime needs a projection helper that can update one stable reasoning row during streaming and finalize it after the complete response arrives, without duplicating rows or writing every token.

## Success Criteria

- Projection helper emits a deterministic record id for the current agent/scope/round reasoning row.
- Running updates set `phase=reasoning`, `public_title=正在思考`, `status=running`, and current text.
- Final update sets completed status and final text/public title.
- Tests cover stable IDs, running/final status, and coalescing throttle behavior.
