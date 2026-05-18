# Remove or justify nested `result` wrapper unwrapping

## Problem Definition

`parse_tool_result` unwraps any dict with a nested `result` dict before applying projection parsing. Static inspection did not show a current production writer that requires this unwrapping for LLM projection, and the branch can revive old wrapped `_mcp_content` image payloads.

## Proposed Solution

Remove the generic nested `result` unwrapping unless direct inspection proves a live persisted-data contract requires it. Add a regression asserting wrapped image content stays inert JSON/text rather than becoming display media.

## Acceptance Criteria

- Generic nested `result` unwrapping is removed or explicitly justified by evidence.
- Wrapped `_mcp_content` image payloads do not produce display files.
- Active `tool-step-payload.v1` and `tool-output.v1` projections still pass.

## Verification Plan

Inspect writers and tests for nested result projection requirements, then run Cortex projection tests after the branch decision.

## Risks

- Removing unwrapping may change display of old manually wrapped payloads, but safer text fallback is acceptable if no current writer depends on it.

## Assumptions

- Current durable payload wrappers use `tool-step-payload.v1` with `llm_content`, not a generic `result` wrapper.
