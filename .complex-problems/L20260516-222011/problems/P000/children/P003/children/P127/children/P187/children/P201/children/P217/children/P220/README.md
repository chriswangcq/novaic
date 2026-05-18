# Add Gemini multimodal provider regression tests

## Problem

The Gemini conversion gap needs tests that fail on the old stringification behavior and pass only when native image parts are emitted.

## Success Criteria

- Tests cover OpenAI-style `image_url` data URL list content.
- Tests assert no image base64 appears in text parts.
- Existing factory provider tests pass.
