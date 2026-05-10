# Add explicit Cortex step projection modes

## Problem Definition

The current step result path uses `include_display=True/False` as a generic switch. Runtime sets it based on whether the tool message belongs to the current round. That still conflates current non-display tool output with explicit display perception, and makes the projection boundary hard to audit.

## Proposed Solution

Introduce explicit projection mode functions in Cortex:

- `format_for_history_llm()`
- `format_for_current_tool_result_llm()`
- `format_for_display_perception_llm()`
- `format_for_monitor()`

Update the Cortex API/bridge/client path to pass a `projection` string. Runtime should pick:

- `history` for non-current tool messages;
- `current_tool_result` for current non-display tool messages;
- `display_perception` only for current explicit `display` tool messages.

Keep the old `include_display` parameter only as a temporary compatibility input at the outer bridge/API edge.

## Acceptance Criteria

- Legacy image `display_files` are text-only for `history`.
- Legacy image `display_files` are text-only for `current_tool_result`.
- Legacy image `display_files` can inline only for `display_perception`.
- Runtime passes `projection` to Cortex and no longer bases the expansion call solely on `include_display`.
- Current `display` messages select `display_perception`.

## Verification Plan

- Run `python -m pytest tests/test_tool_output_projection.py tests/test_step_result_projection.py -q` in `novaic-cortex`.
- Run `python -m pytest tests/test_pr71_no_tool_retry_context_cleanup.py tests/test_runtime_explicit_contracts.py tests/test_pr85_llm_context_smoke_guardrails.py -q` in `novaic-agent-runtime`.

## Risks

- Existing tests may still inspect `include_display`; update them to assert `projection` while keeping compatibility fields if the bridge still sends them.

## Assumptions

- Tool message identity can be read from `tool_name` or `name` when selecting explicit display perception.
