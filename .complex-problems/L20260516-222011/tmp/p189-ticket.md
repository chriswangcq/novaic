# Audit runtime current display selection and active-stack ordering

## Problem Definition

Runtime context assembly must identify current-round `display` tool results by stable metadata, not by message adjacency. The `[Active skill stack]` system message may be appended after the display tool result, but it must not cause display media to be treated as history or dropped before the next LLM call.

## Proposed Solution

Inspect `novaic-agent-runtime/task_queue/utils/step_result_client.py`, `context.py`, and multimodal conversion helpers for how current tool messages are expanded and how display perception markers/media are moved into provider-visible user content. Verify the active-stack-after-display scenario with focused tests. Add a regression test if the current suite does not directly cover this ordering.

## Acceptance Criteria

- Runtime display projection selection code is mapped with file/function evidence.
- Current display tool messages are assigned `display_perception` by current round/tool metadata.
- A following active-stack system message does not downgrade the display result to history or remove media.
- The display tool message remains placeholder/small after media extraction.
- Focused runtime/common tests pass.

## Verification Plan

Run current display/image injection tests, active-stack ordering tests, and context assembly tests. If existing coverage is indirect, add a narrow test where assistant calls `display`, the display tool result is followed by `[Active skill stack]`, and the converted messages still include provider-visible image content.

## Risks

- The code has both step-ref expansion and provider-message conversion stages; this ticket must avoid conflating them.
- Current-round fallback logic for messages without `_round_id` could accidentally attach old display results if not constrained by latest tool call IDs.

## Assumptions

- Cortex projection itself is covered by P188.
- Provider-specific image schema is covered by P190.
