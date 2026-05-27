# Integrate streaming LLM calls into Runtime handler

## Problem

`handle_llm_call` must request streaming from Factory, feed reasoning deltas to the projection helper, and still return the same complete response shape expected by `react_think` and context append.

## Success Criteria

- Handler uses streaming client path for supported Factory calls.
- Handler coalesces projection updates and finalizes reasoning when the stream completes.
- Handler returns `success`, `scope_id`, `round_id`, `response`, and `model` as before.
- Tests prove saga-facing response compatibility and non-streaming/failure behavior remains clear.
