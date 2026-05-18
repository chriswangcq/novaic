# Verify display/media handoff avoids raw image text history

## Problem Definition

Display/media tool results must not leave raw image base64 as ordinary tool text in normal history. Display perception may create a current image message for the model, but historical/default projection must use placeholders or compact text.

## Proposed Solution

Inspect display result handling, multimodal message processing, and prepare-LLM-call media injection behavior. Run focused tests for display chat history, no historical tool image injection, and factory/client multimodal conversion where relevant.

## Acceptance Criteria

- Display/media handling functions are mapped with file/function pointers.
- Evidence shows historical/default display tool result text is compact or placeholder-based, while display perception can inject image through structured image content only when intended.
- Focused tests pass for display handling and no raw base64/image text in history.

## Verification Plan

Use `rg`/`nl` over runtime display handler and multimodal processing code. Run focused pytest files for display chat history, no historical tool image injection, and factory client multimodal preservation.

## Risks

- Some providers require different structured image shapes; this ticket audits runtime handoff, not every factory provider conversion.

## Assumptions

- Provider-specific Gemini/OpenAI conversion was handled in earlier projection work and will only be smoke-verified here if tests are local.
