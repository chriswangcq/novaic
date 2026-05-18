# LLMCall contract provider payload source verified

## Summary

Mapped the pure LLM call contract layer and tightened the explicit contract test so provider `tools` are asserted alongside provider `messages`. The layer uses explicit payload fields plus injected preprocessing dependencies; no hidden context reads were found.

## Done

- Mapped `LLMCallInput.from_payload` at `novaic-agent-runtime/task_queue/contracts/llm_call.py:37`.
- Confirmed payload `messages` are required, type-checked, and deep-copied at `llm_call.py:44-55`.
- Confirmed payload `tools` are type-checked and deep-copied at `llm_call.py:49-57`.
- Mapped `prepare_llm_call` at `llm_call.py:115`.
- Confirmed provider messages start from `deepcopy(source.messages)` and flow through injected `expand_messages_for_llm`, `sanitize_context`, and `process_multimodal_messages` at `llm_call.py:128-137`.
- Confirmed provider tools are copied from `source.tools` at `llm_call.py:143`.
- Tightened `test_prepare_llm_call_has_injected_preprocessing_dependencies` to assert `prepared.tools` comes from explicit payload tools.

## Verification

- `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`
- Result: `13 passed in 0.14s`.

## Known Gaps

- None for the pure contract layer. Handler-level transport delegation remains sibling `P172`.

## Artifacts

- Modified `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`.
