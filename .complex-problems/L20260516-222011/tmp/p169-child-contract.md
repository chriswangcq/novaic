# LLMCall contract provider payload source map

## Problem

`contracts/llm_call.py` parses `llm.call` payloads and prepares provider messages/tools. It must not read hidden context or invent messages/tools outside explicit input and injected preprocessing functions.

## Success Criteria

- `LLMCallInput.from_payload` and `prepare_llm_call` are mapped with line pointers.
- The explicit source of `messages` and `tools` in the prepared provider call is documented.
- Tests prove preprocessing is injected and ordered, not hidden inside the business transport.
- Any hidden source of context/messages/tools is fixed or split.
