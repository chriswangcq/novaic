# Audit runtime step-ref projection selection

## Problem Definition

Runtime must choose the correct Cortex formatted-read projection for each tool step before LLM assembly. Current-round `display` must request `display_perception`; historical `display` must request `history`; current non-display tools must request `current_tool_result`.

## Proposed Solution

Inspect `novaic-agent-runtime/task_queue/utils/step_result_client.py`, especially `_projection_for_tool_message`, `_latest_tool_call_ids`, `_tool_names_by_call_id`, and `expand_messages_for_llm`. Verify existing tests or add focused tests that assert projection values passed into `read_step_formatted` for current display, historical display, and current shell/non-display messages.

## Acceptance Criteria

- Projection selection code is mapped.
- Current display tool messages use `display_perception`.
- Historical display tool messages use `history`.
- Current non-display tool messages use `current_tool_result`.
- Focused tests pass.

## Verification Plan

Run runtime tests that assert `read_step_formatted` projection arguments, especially `test_pr71_no_tool_retry_context_cleanup.py` and `test_no_historical_tool_image_injection.py`. Add a small unit test if a branch is not directly covered.

## Risks

- Tool name can come from assistant tool calls, tool message metadata, or fallback maps; tests should cover at least the active production path.
- Messages without `_round_id` can fall back to latest tool call IDs; this fallback must not select stale display steps.

## Assumptions

- Cortex `/v1/steps/read_formatted` supports the requested projection names, covered by P188.
