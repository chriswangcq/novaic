# Ticket: audit display tool history output

## Problem Definition

The display tool's own tool observation should be compact and non-binary. It must not place raw image bytes, base64, or `data:image` URLs into text history.

## Proposed Solution

- Locate the runtime display tool handler and its tests.
- Verify what content is returned to tool history for image blobs.
- Patch active display output if it includes image bytes as text.
- Run focused tests for display chat-history/tool-output behavior.

## Acceptance Criteria

- Display image tool observations are compact text, not raw image payloads.
- No active display tool test expects base64 in tool text.
- Focused display handler tests pass.

## Verification Plan

- Inspect runtime display handler and display-related tests.
- Run targeted display handler tests.
- Search display handler paths for `data:image` or raw base64 text projection.

## Risks

- Display may intentionally fetch image bytes for model perception; this ticket only concerns the tool observation text, not the model image block.

## Assumptions

- Image perception handoff is solved by sibling `P055`; `P054` should not overreach into LLM context assembly.
