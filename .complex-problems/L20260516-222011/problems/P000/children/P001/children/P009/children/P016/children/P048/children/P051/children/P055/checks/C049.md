# Check: LLM Context Assembly Preserves Displayed Images

## Summary

Success. Result `R039` proves the display image is not lost after public tool content sanitization: the durable payload remains the image source for Cortex projection and runtime multimodal conversion.

## Evidence

- Cortex test now covers `tool-step-payload.v1` display payload parsing and projection.
- Runtime tests cover public display placeholder content, durable raw image preservation, and image injection before following system messages.
- Focused runtime and Cortex tests passed.

## Criteria Map

- Display durable payload with image `_mcp_content` is resolved into display perception content: satisfied by the new Cortex projection test.
- The processed request contains provider-native image content: satisfied by runtime multimodal tests asserting OpenAI `image_url` user content is inserted.
- Public placeholder content is not the only source of truth: satisfied by tests that verify public content has no image `data` while durable payload retains it.

## Execution Map

- `T045` added missing projection coverage and verified the runtime/Cortex handoff after the `P054` sanitization change.
- No further code changes were needed in context assembly beyond the `P054` durable payload handoff.

## Stress Test

- Plausible failure mode: a following system message appears after the display tool result, causing the image user message to be inserted in the wrong place or dropped. Existing focused runtime test covers this and asserts message order: assistant, tool placeholder, user image, system.

## Residual Risk

- Low for runtime/Cortex assembly. Provider-specific logging/redaction is still open under `P056`.

## Result IDs

- R039
