# P196 Check: factory provider request adapter media preservation

## Summary

Success. R178 solves P196: Factory provider adapter paths are mapped, OpenAI-compatible outbound payload preservation now has direct regression coverage, and existing Anthropic image conversion coverage remains passing.

## Evidence

- `OpenAIProvider.chat` sends `request.messages` directly in provider JSON.
- New test captures the fake provider POST payload and asserts `image_url` remains structured.
- Existing Anthropic test proves `image_url` data URLs convert to native Anthropic image blocks.
- Full `test_chat_routes.py` passed with the new regression.

## Criteria Map

- Factory provider adapter/client modules are mapped: satisfied by R178.
- OpenAI-compatible `image_url` content survives to provider request: satisfied by `test_openai_provider_preserves_structured_image_url_payload`.
- Raw base64 is not moved into text fields: satisfied by recursive text-field assertion.
- Focused adapter tests pass: `12 passed in 0.22s`.

## Execution Map

- T184 was executed as one adapter-focused audit.
- One test was added because the OpenAI-compatible adapter had no direct outbound multimodal preservation test.

## Stress Test

- The new test includes both an image item and text item in one user content array, catching accidental list-to-string or image-to-text flattening.

## Residual Risk

- Factory logging/detail serialization is not judged here and remains P197.

## Result IDs

- R178
