# Cortex projection inventory ticket

## Problem Definition

Cortex projection parsing/formatting is the first boundary where raw tool payloads can leak into model history. We need a focused inventory of Cortex branches and their status.

## Proposed Solution

Inspect `step_result_projection.py`, Cortex API projection call sites, and related tests only as references. Classify branches as active, compatibility, test-only, or stale with line evidence. Do not edit code.

## Acceptance Criteria

- Covers `parse_tool_result`, `_parse_tool_output_v1`, `format_for_history_llm`, `format_for_display_perception_llm`, truncation, artifacts, display files, and wrapper parsing.
- Produces exact file/line references and cleanup candidates.
- Does not modify code.

## Verification Plan

Use `rg`, `nl`, and focused reads. The result must be a classification table suitable for downstream cleanup.

## Risks

- Persisted historical payload shapes may require compatibility parsing even if no current producer emits them.

## Assumptions

- This ticket is read-only inventory.
