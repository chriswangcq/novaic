# Factory provider request adapter media preservation result

## Summary

Audited Factory provider adapter media preservation and added a focused OpenAI-compatible provider regression. OpenAIProvider passes `ProviderChatInput.messages` into provider JSON unchanged, preserving structured `image_url` content. Existing Anthropic coverage verifies conversion from OpenAI-style `image_url` to Anthropic native image blocks.

## Done

- Mapped Factory provider adapter code:
  - `novaic-llm-factory/factory/providers.py`
    - `OpenAIProvider.chat`
    - `AnthropicProvider._convert_content`
    - `AnthropicProvider.chat`
  - `novaic-llm-factory/factory/contracts.py`
    - `ProviderChatInput`
- Added `test_openai_provider_preserves_structured_image_url_payload`.
- Confirmed OpenAI-compatible provider payload keeps:
  - `{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}`
  - text content as a separate text item.
- Confirmed the image base64 is not copied into any `text` field.

## Verification

```bash
pytest -q novaic-llm-factory/tests/test_chat_routes.py
```

Result: `12 passed in 0.22s`.

## Known Gaps

- Log/detail serialization is P197.

## Artifacts

- `novaic-llm-factory/factory/providers.py`
- `novaic-llm-factory/factory/contracts.py`
- `novaic-llm-factory/tests/test_chat_routes.py`
