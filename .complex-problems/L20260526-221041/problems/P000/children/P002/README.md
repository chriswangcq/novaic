# Stream reasoning through Runtime aggregation and activity projection

## Problem

Runtime currently waits for a complete Factory response, then projects reasoning once during context append. It needs to consume Factory streaming output, aggregate the final response for saga compatibility, and emit bounded running/final reasoning updates through existing Agent Monitor projection entities.

## Success Criteria

- Runtime can request and consume streaming chat completions from Factory.
- Runtime returns a complete OpenAI-style response to existing saga decision code.
- Runtime emits stable same-record reasoning updates with `status=running` and a final completed state.
- Projection writes are coalesced/bounded and do not write one row per token.
- Durable context append semantics remain final-response only.
