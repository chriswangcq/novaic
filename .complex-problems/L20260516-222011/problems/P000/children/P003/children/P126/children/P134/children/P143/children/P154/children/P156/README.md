# Cortex prepare_for_llm read model authority

## Problem

The Cortex `/v1/context/prepare_for_llm` endpoint must assemble context from the ContextEvent read model, not from `context.jsonl`.

This belongs under `P154` because it is the service-side authority boundary for model context.

## Success Criteria

- Endpoint and helper source path are mapped.
- Evidence proves `prepare_context`/read-model is used.
- Evidence proves `read_context` is not called by the endpoint.
