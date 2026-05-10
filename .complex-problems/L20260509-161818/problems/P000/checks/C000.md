# Runtime current-round projection boundary check

## Status

success

## Result IDs

- R000

## Evidence

- `novaic-agent-runtime/task_queue/contracts/llm_call.py` passes `current_round_id=source.round_id` to `expand_messages_for_llm`.
- `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py` asserts the injected expand dependency receives `current_round_id == "round-1"`.
- Test command: `python -m pytest tests/test_runtime_explicit_contracts.py tests/test_pr85_llm_context_smoke_guardrails.py tests/test_pr71_no_tool_retry_context_cleanup.py -q`
- Test result: `24 passed in 0.11s`.

## Criteria Map

- `prepare_llm_call()` passes `current_round_id=source.round_id` to `expand_messages_for_llm`: satisfied by code change.
- Unit tests assert the injected dependency receives the current round ID: satisfied by explicit test assertion.
- Nearby Runtime contract tests still pass: satisfied by 24 passing tests.
- The change is small and deterministic, with no hidden dependencies: satisfied because the value comes from `LLMCallInput.source.round_id` and is injected as a kwarg.

## Execution Map

- Problem analyzed: missing current-round argument at the Runtime LLM preprocessing boundary.
- Ticket executed: added one kwarg to the dependency call and one contract assertion.
- Verification executed: targeted Runtime contract and context guard tests.

## Stress Test

- If a future refactor removes the kwarg, `test_prepare_llm_call_has_injected_preprocessing_dependencies` fails.
- If historical display/tool content attempts to re-enter through step-ref expansion, Cortex now has the explicit current round input needed by the projection boundary.

## Residual Risk

- Broader shell/display migration still has remaining tickets. This check only certifies the current-round projection boundary ticket.
