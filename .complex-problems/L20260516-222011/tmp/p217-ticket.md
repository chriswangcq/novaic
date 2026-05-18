# Implement and test Google/Gemini multimodal conversion

## Problem Definition

Google/Gemini provider conversion currently turns non-string user content into `str(content)`, which loses structured multimodal image content and may place data URLs into text.

## Proposed Solution

Split into implementation and verification: add provider-level conversion from OpenAI-style multimodal content to Gemini native parts, then add tests proving image data becomes `inlineData` and does not appear inside text parts.

## Acceptance Criteria

- User list content with text and `image_url` data URL converts to Gemini parts.
- Image base64 appears only in `inlineData.data`, not text.
- Existing provider behavior for plain text, tools, and OpenAI/Anthropic tests remains intact.
- Tests cover the Google provider path.

## Verification Plan

Add focused factory provider tests, run them, and rerun existing factory chat/log tests.

## Risks

- Gemini REST field casing can be provider-specific; choose a consistent request shape and pin it in tests.
- Non-data image URLs cannot be sent directly as Gemini inline bytes; represent them as text placeholders unless a File API path exists.

## Assumptions

- Runtime sends OpenAI-style `image_url` data URLs after display perception conversion.
