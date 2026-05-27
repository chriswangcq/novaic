# Add LLM Factory streaming transport contract

## Problem

LLM Factory currently accepts a `stream` request flag but does not implement streaming provider transport. Reasoning streaming needs Factory to expose a clear, normalized stream for supported providers while preserving the existing non-streaming response path.

## Success Criteria

- Factory has a provider-level streaming contract for OpenAI-compatible chat completions.
- Streaming chunks preserve reasoning/content/tool-call deltas in a normalized shape Runtime can consume.
- Non-streaming chat completions remain compatible and covered by tests.
- Unsupported providers fail clearly rather than silently pretending to stream.
