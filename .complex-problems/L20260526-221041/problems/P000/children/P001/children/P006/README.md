# Wire Factory chat route streaming response and logging

## Problem

The Factory route must honor `stream=true` by returning a streaming response from supported providers and must keep `stream=false` behavior unchanged. Unsupported provider streams should fail clearly.

## Success Criteria

- `/v1/chat/completions` returns streaming chunks when `stream=true` for OpenAI-compatible providers.
- Unsupported native provider streaming returns a clear error instead of silently falling back.
- Log records are completed or failed consistently for streaming calls.
- Existing non-streaming route tests continue to pass.
