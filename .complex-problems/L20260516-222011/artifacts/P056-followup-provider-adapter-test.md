# Add direct provider adapter image payload tests

## Problem

The provider image payload contract cannot be closed from static inspection alone. Add and run a focused LLM Factory unit test that directly exercises provider adapter image handling, especially the Anthropic conversion path for an OpenAI-style data URL image block.

## Success Criteria

- A focused test proves that an OpenAI-style `image_url` data URL is converted to Anthropic-native image content with structured `source.type=base64`, `media_type`, and `data`.
- The test proves the converted content is not flattened into a plain text base64 string.
- Existing Factory log redaction tests still pass.
- Focused LLM Factory tests are run and recorded.
