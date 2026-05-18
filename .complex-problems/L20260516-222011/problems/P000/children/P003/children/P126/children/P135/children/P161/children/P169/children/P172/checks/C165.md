# LLM handler transport delegation boundary check

## Summary

`P172` is solved. The handler maps cleanly as orchestration: parse explicit payload, inject preprocessing dependencies into `prepare_llm_call`, then pass the prepared request to `LLMBusiness.call`. Static guards and focused tests prove there is no active `read_context`/`context.read` provider-message authority in this handler.

## Evidence

- `LLMCallInput.from_payload`: `novaic-agent-runtime/task_queue/handlers/llm_handlers.py:93`.
- Preprocessing dependency imports and injection: `llm_handlers.py:117-127`.
- Transport setup: `llm_handlers.py:129-134`.
- Final transport call with prepared fields: `llm_handlers.py:136-141`.
- Static guards: `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py:241-259`.
- Focused tests: `22 passed in 0.13s`.

## Criteria Map

- Handler line pointers identified: satisfied.
- Tests/static guards prove no `read_context`/`context.read`: satisfied.
- Handler preprocessing dependencies are explicit: satisfied by `prepare_llm_call(... expand_messages_for_llm=..., sanitize_context=..., process_multimodal_messages=...)`.
- Focused handler tests run: satisfied.

## Execution Map

- `T157` one-go executed after `P169` split.
- No code changes were necessary; existing guards and source mapping were sufficient.
- Recorded result `R151`.

## Stress Test

If handler code starts calling `read_context` or `context.read`, `test_llm_call_handler_does_not_read_cortex_context_as_authority` fails. If it bypasses `LLMCallInput.from_payload` or `prepare_llm_call`, `test_runtime_saga_and_llm_handlers_delegate_to_explicit_contract_modules` fails.

## Residual Risk

- Business transport internals are not part of this leaf. The handler passes prepared data into transport; transport-only constraints are guarded elsewhere.

## Result IDs

- R151
