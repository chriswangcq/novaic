# ReactThink llm.call payload builder map

## Problem

`react_think` is responsible for moving the prepared Cortex snapshot into the `llm.call` task payload. The field copy contract must be explicit so final LLM calls do not accidentally use stale local context fields.

## Success Criteria

- `novaic-agent-runtime/task_queue/contracts/react_think.py` is mapped for `build_llm_call_payload`.
- The fields copied from `prepare_context_result` into the LLM call payload are listed with line pointers.
- Existing or added tests prove `messages` and `tools` are copied from the prepare result, not from saga-local continuity fields.
- Any ambiguous local fallback in this builder is fixed or split.
