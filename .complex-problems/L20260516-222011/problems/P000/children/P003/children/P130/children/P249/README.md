# Audit provider adapter native media formats

## Problem

LLM factory provider adapters must convert image content to provider-native media payloads rather than plain text base64. This belongs under P130 because it is the final API boundary where image bytes are legitimate.

## Success Criteria

- OpenAI/Anthropic/Gemini provider media conversion code is mapped, or absent providers are explicitly scoped.
- Focused tests prove data URL image content is converted to native provider structures, including Gemini inlineData where relevant.
- No provider request test expects raw base64 as a plain text message.
