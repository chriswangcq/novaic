# Gemini multimodal provider regression test result

## Summary

Added a focused Gemini provider regression test that proves OpenAI-style data URL image content is converted into Gemini native `inlineData` parts instead of leaking base64 into text parts.

## Done

- Updated `novaic-llm-factory/tests/test_chat_routes.py` with `test_google_provider_converts_data_url_images_to_inline_data`.
- The test monkeypatches the provider HTTP client, captures the outgoing Gemini request, and verifies the exact `contents[0].parts` shape.
- The test asserts the returned provider response still converts back to OpenAI-compatible chat completion content.
- The test asserts `/9j/SECRETBASE64` does not appear in any outgoing text value.

## Verification

- Ran `pytest -q novaic-llm-factory/tests/test_chat_routes.py novaic-llm-factory/tests/test_log_routes.py`.
- Result: `17 passed in 0.23s`.

## Known Gaps

- No known gap for this ticket. This test pins the Gemini request projection contract that was implemented in the prior ticket.

## Artifacts

- `novaic-llm-factory/tests/test_chat_routes.py`
