# P192 Check: runtime step-ref display projection selection

## Summary

Success. R174 satisfies the projection-selection problem: it maps the helper functions and proves with direct call-argument tests that current display, historical display, and current non-display tools select the intended Cortex projection.

## Evidence

- `expand_messages_for_llm` calls `_projection_for_tool_message` for each tool message with a `step_ref`.
- `_projection_for_tool_message` computes currentness from `_round_id`, `current_round_id`, and latest assistant tool call fallback, then selects `display_perception` only when the tool identity is `display`.
- Tests directly inspect `read_step_formatted(..., projection=...)` calls rather than inferring from final text.

## Criteria Map

- Projection selection code is mapped: satisfied by the function list in R174.
- Current display tool messages use `display_perception`: covered by tests using `tool_name`, `_metadata.tool`, and assistant tool-call inference.
- Historical display tool messages use `history`: covered by old-round and old-display-after-new-tool-block tests.
- Current non-display tool messages use `current_tool_result`: covered by the new-tool-block shell assertion.
- Focused tests pass: `14 passed` and `9 passed` recorded in R174.

## Execution Map

- T179 was executed as one bounded audit of the runtime projection-selection helper.
- No code changes were needed.

## Stress Test

- The stale-display failure mode is covered: after a newer shell tool block, the older display step is formatted with `history`, while the newer shell step is formatted with `current_tool_result`.
- The missing tool metadata failure mode is covered: assistant `tool_calls` can infer `display_perception` even when the tool message lacks direct display metadata.

## Residual Risk

- P192 does not prove media extraction or provider conversion; those are explicitly separated into P193 and P190.

## Result IDs

- R174
