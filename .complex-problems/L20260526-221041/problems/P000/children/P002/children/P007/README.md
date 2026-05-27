# Add Runtime Factory stream parser and final response aggregator

## Problem

Runtime Factory client must consume Factory normalized SSE chunks and aggregate them into a complete OpenAI-style chat completion response compatible with current saga code.

## Success Criteria

- Runtime can parse Factory SSE `data:` lines with `type=delta`, `type=done`, and `type=error`.
- Aggregator builds final assistant message fields for `content`, `reasoning_content`, `tool_calls`, `finish_reason`, `usage`, and `x_factory` where present.
- Unit tests cover reasoning/content accumulation, tool-call argument fragments, terminal/error handling, and non-streaming client behavior.
