# Gemini multimodal provider regression tests success check

## Summary

Success. Result R204 satisfies P220: the factory test suite now includes a Gemini provider request-capture regression that covers OpenAI-style data URL image list content, verifies native `inlineData` emission, and rejects base64 leakage into text parts.

## Evidence

- Result R204 added `test_google_provider_converts_data_url_images_to_inline_data` in `novaic-llm-factory/tests/test_chat_routes.py`.
- The test captures the exact HTTP JSON payload emitted by `GoogleProvider.chat`.
- The test asserts the payload parts equal an `inlineData` image part followed by a text part.
- The test asserts `/9j/SECRETBASE64` does not appear in any recursive `text` value in the outgoing payload.
- Factory chat/log tests passed: `17 passed in 0.23s`.

## Criteria Map

- Tests cover OpenAI-style `image_url` data URL list content: covered by the test input content list with `{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,/9j/SECRETBASE64"}}` plus a text block.
- Tests assert no image base64 appears in text parts: covered by recursive `_text_values(captured["json"])` assertion.
- Existing factory provider tests pass: covered by `pytest -q novaic-llm-factory/tests/test_chat_routes.py novaic-llm-factory/tests/test_log_routes.py` producing 17 passing tests.

## Execution Map

- T210 was classified as `one_go` because it was a bounded test addition.
- R204 records the concrete test addition and the exact verification command/result.
- The implementation was not changed in this ticket; this ticket only pinned the provider conversion contract from the prior sibling implementation ticket.

## Stress Test

The plausible regression is old Gemini behavior stringifying mixed content into a text part, which would place `/9j/SECRETBASE64` under `text`. The new test fails that behavior because it requires exact `inlineData` shape and globally rejects the base64 marker in text values.

## Residual Risk

Non-blocking: this test pins the internal provider payload contract using a monkeypatched HTTP client, not a live Gemini API call. That is appropriate for deterministic unit coverage and avoids network/provider flake. Live API drift would be caught by integration smoke tests outside this focused ticket.

## Result IDs

- R204
