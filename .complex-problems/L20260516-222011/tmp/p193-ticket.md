# Audit active-stack-after-display media preservation

## Problem Definition

After runtime expands a current `display` step, context assembly must preserve the display media even if an `[Active skill stack]` system message appears immediately after the display tool result. The original tool result should be reduced to a placeholder, and the image should be moved into provider-visible multimodal content.

## Proposed Solution

Inspect the runtime context and multimodal helpers that sanitize `_mcp_content`, preserve `_projection`, and convert display perception media into user image messages. Verify the exact active-stack-after-display ordering with focused tests. Add or tighten tests if the current coverage does not assert both placeholder-only tool content and image message preservation.

## Acceptance Criteria

- Context/multimodal media extraction code is mapped.
- Display media survives when a following active-stack system message is present.
- The display tool message is placeholder-only and contains no raw base64 data after conversion.
- The converted message order is deterministic and keeps the following system message.
- Focused runtime tests pass.

## Verification Plan

Run `test_no_historical_tool_image_injection.py` and any context assembly tests that exercise `prepare_llm_call`, `sanitize_context`, and `process_multimodal_messages`. Add a narrow regression test if placeholder-only content or following system preservation is not directly asserted.

## Risks

- The media extraction stage might be provider-aware; this ticket must prove the runtime-internal conversion and leave final provider schema to P190.
- Sanitization could accidentally strip `_projection` before multimodal conversion.

## Assumptions

- Step-ref projection selection is already covered by P192.
