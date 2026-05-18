# ReactThink llm.call payload builder verified

## Summary

Mapped `build_llm_call_payload` and tightened its explicit-contract test so prepared snapshot messages/tools are distinguished from stale saga-local tools. No local context fallback was found inside the builder.

## Done

- Mapped `ReactThinkInput` fields at `novaic-agent-runtime/task_queue/contracts/react_think.py:16`; saga-local `tools` exists at line 29 but is not used by `build_llm_call_payload`.
- Mapped `build_llm_call_payload` at `novaic-agent-runtime/task_queue/contracts/react_think.py:98`.
- Confirmed prepared snapshot authority: `messages` are copied from `prepare_context_result` at `react_think.py:107`, and `tools` are copied from `prepare_context_result` at `react_think.py:109`.
- Documented metadata copied from saga source: `scope_id`, `agent_root_scope_id`, `wake_scope_path`, `round_id`, `model`, `agent_id`, `subagent_id`, `user_id`, and `session_generation` at `react_think.py:103-113`.
- Tightened `test_react_think_payload_builders_use_explicit_snapshot` to include a stale local tool in `ReactThinkInput` and assert `llm.call` receives only prepared-result tools.

## Verification

- `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`
- Result: `13 passed in 0.13s`.

## Known Gaps

- None for this builder leaf. Handler/provider request assembly remains the sibling problem `P169`.

## Artifacts

- Modified `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`.
