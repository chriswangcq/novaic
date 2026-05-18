# Implement provider adapter image payload test

## Problem

Add the missing LLM Factory provider adapter test and run the focused verification. This follow-up exists because the previous ticket attempt only prepared the ticket state and did not perform the implementation.

## Success Criteria

- A test directly exercises the Anthropic provider conversion path with a synthetic OpenAI-style `data:image/...;base64,...` image URL content block.
- The test asserts the adapter returns a provider-native image block with structured `source.type=base64`, `media_type`, and `data`.
- The test asserts the image payload was not converted into a plain text base64 block.
- Existing chat-route image redaction tests pass together with the new provider adapter test.
