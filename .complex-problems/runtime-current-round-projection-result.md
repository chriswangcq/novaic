# Runtime current-round projection boundary result

## Summary

Implemented the bounded runtime-to-Cortex current-round projection boundary. `prepare_llm_call()` now passes `source.round_id` as `current_round_id` into the injected `expand_messages_for_llm` dependency, so Cortex projection can distinguish current-round tool outputs from historical attachments/resources.

## Done

- Updated `novaic-agent-runtime/task_queue/contracts/llm_call.py` to pass `current_round_id=source.round_id` at the LLM preprocessing boundary.
- Updated `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py` to assert the injected expand dependency receives `current_round_id`.
- Kept the change at the explicit dependency boundary instead of adding hidden global state.

## Verification

- Ran `python -m pytest tests/test_runtime_explicit_contracts.py tests/test_pr85_llm_context_smoke_guardrails.py tests/test_pr71_no_tool_retry_context_cleanup.py -q` in `novaic-agent-runtime`.
- Result: `24 passed in 0.11s`.

## Residual Risk

- This ticket only wires the round id into the runtime boundary. Further tickets are still needed to complete the broader shell/display architecture migration and old direct-tool cleanup.
