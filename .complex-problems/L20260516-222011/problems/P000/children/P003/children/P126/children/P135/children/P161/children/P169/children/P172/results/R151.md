# LLM handler transport delegation boundary verified

## Summary

Mapped `llm_handlers.handle_llm_call` and verified it delegates provider request preparation to explicit contract code before calling the business transport. No direct `read_context` or provider-message reconstruction path was found in the handler.

## Done

- Mapped payload parsing through `LLMCallInput.from_payload` at `novaic-agent-runtime/task_queue/handlers/llm_handlers.py:93`.
- Mapped explicit preprocessing dependency injection into `prepare_llm_call` at `llm_handlers.py:117-127`.
- Mapped transport client creation at `llm_handlers.py:129-134`.
- Mapped final `LLMBusiness.call` using `prepared.messages`, `prepared.model`, `prepared.tools`, and `prepared.provider` at `llm_handlers.py:136-141`.
- Verified static guards in `test_runtime_explicit_contracts.py` assert the handler delegates to `LLMCallInput.from_payload` and `prepare_llm_call`, does not contain `read_context` or `context.read`, and does not inline multimodal processing after sanitization.

## Verification

- `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/test_runtime_explicit_contracts.py novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py`
- Result: `22 passed in 0.13s`.

## Known Gaps

- None for handler transport delegation. The pure contract layer was closed separately by `P171`.

## Artifacts

- No code changes were required for this leaf.
