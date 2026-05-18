# Audit current display provider-media projection

## Problem Definition

Current-round `display` results must be usable by the LLM provider as image/media input while the original tool result message remains placeholder-only. This ticket audits the display path from Cortex step projection through runtime context assembly and provider multimodal conversion, and fixes or splits any branch where display output stays as plain text or raw base64.

## Proposed Solution

Trace the current display result path across `novaic-cortex/novaic_cortex/step_result_projection.py`, `novaic-cortex/novaic_cortex/step_result_client.py`, and runtime LLM/context assembly code. Verify the intended contract with focused tests: tool message content should remain a small placeholder such as `OK`, while a separate provider/user media content item is inserted for the current displayed blob. If the path is already correct, record evidence. If any conversion branch is missing or ambiguous, implement a scoped fix or split the exact missing branch into follow-up tickets.

## Acceptance Criteria

- Current display projection and provider multimodal conversion code paths are mapped with file/function evidence.
- Current display emits provider-consumable image/media input in the assembled LLM request.
- The corresponding tool result message remains placeholder-only and does not contain raw base64 or large artifact payload text.
- Focused regression tests prove current display still works when an active-stack system message follows the display result.
- Any failed branch is either fixed in this ticket or split into a smaller follow-up with an explicit boundary.

## Verification Plan

Run focused Cortex and runtime/common tests covering display current projection, provider media conversion, and context assembly ordering. If necessary, add a regression test that simulates shell screenshot artifact -> display tool result -> next LLM request and asserts provider image input exists while the tool message is small.

## Risks

- Provider-specific media schemas may differ; the audit must distinguish internal `_mcp_content` shape from final provider request shape.
- The active stack system message appears after tool results in context, so tests must prove media attachment selection is keyed by current round/tool metadata rather than positional adjacency.
- Historical display outputs may intentionally be manifest-only; do not accidentally make old history rehydrate large images.

## Assumptions

- P185 covers only current-round display media handoff. Historical display/artifact manifest behavior is handled by sibling P186.
- Shell output media-like text is already covered by P184.
