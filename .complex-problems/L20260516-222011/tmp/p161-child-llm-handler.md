# LLM handler provider request assembly map

## Problem

`llm_handlers` and `contracts/llm_call.py` turn the `llm.call` payload into the final provider request. That layer must preserve prepared messages/tools and must not rehydrate provider messages from Cortex projections or other local state.

## Success Criteria

- `novaic-agent-runtime/task_queue/handlers/llm_handlers.py` is mapped around `LLMCallInput.from_payload` and `prepare_llm_call`.
- `novaic-agent-runtime/task_queue/contracts/llm_call.py` is mapped for provider-message/tool assembly.
- Tests or static guards prove final provider request `messages` and `tools` come from the explicit `llm.call` payload.
- Any legacy context source reaching provider messages is fixed or split.
