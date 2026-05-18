# Map runtime step result expansion path

## Problem

Runtime LLM preparation must expand `step_ref` tool results through explicit Cortex projections, not by loading raw durable payloads into ordinary history.

## Success Criteria

- File/function path for LLM call preparation and `step_ref` expansion is mapped.
- Projection selection inputs are identified (`round_id`, tool name, tool call id, current/latest status).
- Evidence shows raw durable payloads are not directly inserted by this path.
