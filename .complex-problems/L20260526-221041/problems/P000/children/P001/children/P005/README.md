# Implement OpenAI-compatible streaming chunk normalization

## Problem

Factory providers need a small, testable contract that turns OpenAI-compatible SSE chat completion chunks into normalized Python dictionaries preserving content, reasoning, tool-call deltas, finish reason, and usage where available.

## Success Criteria

- `OpenAIProvider` exposes a streaming method for OpenAI-compatible chat completions.
- The parser handles `data: {...}` SSE lines and `[DONE]` termination.
- Reasoning deltas are extracted from common fields such as `reasoning_content`, `reasoning`, and provider-specific delta aliases.
- Unit tests cover content, reasoning, tool-call delta, done, and error classification behavior.
