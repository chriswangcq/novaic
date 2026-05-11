# Project top-level step_ref for tool results

## Problem Definition

Runtime LLM expansion requires top-level `step_ref` on tool messages, but Cortex context event projection only stores tool payload refs inside `_metadata.payload_ref`.

## Proposed Solution

Update `ToolStepRecorded` projection to copy a string `payload_ref` to top-level `step_ref` while preserving `_metadata.payload_ref`.

## Acceptance Criteria

- Every projected tool message with a payload ref has `step_ref`.
- Existing metadata payload ref remains intact.
- Tests cover ordinary, multiple, and orphan tool-result projection paths.

## Verification Plan

- Update Cortex context projection tests.
- Run focused Cortex projection tests.

## Risks

- Tests that compare exact message dicts need deliberate updates.

## Assumptions

- `payload_ref` is the durable join key that should become `step_ref`.
