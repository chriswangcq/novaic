# LLM handler transport delegation boundary map

## Problem

`handlers/llm_handlers.py` should delegate payload parsing and provider preparation to explicit contract code, then call the LLM business transport. It must not read Cortex context or reconstruct provider messages directly.

## Success Criteria

- `llm_handlers.py` is mapped for `LLMCallInput.from_payload`, `prepare_llm_call`, and final transport call.
- Static or behavioral tests prove handler code does not call `read_context` or `context.read`.
- Focused handler tests are run.
- Any direct provider-message reconstruction in the handler is fixed or split.
