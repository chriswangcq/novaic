# Verify LLM tool schema and policy payload boundary

## Problem Definition

The LLM-visible tool policy/schema surface must keep payload inspection explicit and bounded. Payload read/search/summarize/qa should be discoverable as explicit tools/capabilities, while normal shell/display behavior remains bounded.

## Proposed Solution

Inspect `tool_surface_policy.py`, tool schema tests, and payload tool schema limit tests. Run focused schema/policy tests.

## Acceptance Criteria

- Tool surface policy explicitly lists payload inspection tools/capabilities.
- Schema tests confirm payload tool parameters and bounds.
- No active policy/schema path implies automatic full payload expansion in normal context.

## Verification Plan

Use `rg`/`nl` over runtime policy and Cortex schema tests. Run targeted pytest files for tool schemas and runtime tool surface boundary.

## Risks

- Some generated schema output may be produced dynamically; tests should be trusted only with code pointer evidence.

## Assumptions

- Shell CLI guidance is handled separately by `P240`.
