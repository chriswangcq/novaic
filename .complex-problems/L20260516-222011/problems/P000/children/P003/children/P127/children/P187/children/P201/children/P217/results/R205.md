# Google/Gemini multimodal provider conversion result

## Summary

Closed the Google/Gemini multimodal provider conversion branch by combining implementation result R203 and regression-test result R204. Gemini user list content now converts to native text/image parts, with tests pinning that data URL image base64 is carried only in `inlineData.data` and not text.

## Done

- Implemented `GoogleProvider._convert_content_parts` and `_inline_data_from_data_url` in `novaic-llm-factory/factory/providers.py`.
- Routed Google user message conversion through structured Gemini parts instead of `str(content)` fallback for list multimodal content.
- Added route/provider regression test `test_google_provider_converts_data_url_images_to_inline_data` in `novaic-llm-factory/tests/test_chat_routes.py`.
- Preserved existing OpenAI and Anthropic multimodal behavior while extending Google/Gemini conversion.

## Verification

- R203 smoke-converted a Gemini message with image data URL plus text and confirmed inline image part plus text part.
- R204 ran `pytest -q novaic-llm-factory/tests/test_chat_routes.py novaic-llm-factory/tests/test_log_routes.py`.
- Test result: `17 passed in 0.23s`.

## Known Gaps

- No known blocking gaps for this branch. Live Gemini API behavior is not exercised here; deterministic provider-unit coverage pins the request contract.

## Artifacts

- R203
- R204
- `novaic-llm-factory/factory/providers.py`
- `novaic-llm-factory/tests/test_chat_routes.py`
