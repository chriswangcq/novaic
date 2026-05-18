# Add Google/Gemini multimodal provider regression tests

## Problem Definition

The Google provider fix must be pinned by tests that would fail on the old `str(content)` behavior and verify base64 is not placed into text parts.

## Proposed Solution

Add a provider `chat` capture test for a user message with OpenAI-style `image_url` data URL and text content. Assert the outgoing Gemini request contains `inlineData` image part and text part, and no text part contains the image base64.

## Acceptance Criteria

- Test captures Google provider request body.
- Test asserts native inline image part shape.
- Test asserts no image base64 appears in text parts.
- Existing factory chat/log tests pass.

## Verification Plan

Run `pytest -q novaic-llm-factory/tests/test_chat_routes.py novaic-llm-factory/tests/test_log_routes.py`.

## Risks

- Field casing in the test must match the implemented provider request contract.

## Assumptions

- Current provider request uses camelCase fields such as `inlineData` and `mimeType`.
