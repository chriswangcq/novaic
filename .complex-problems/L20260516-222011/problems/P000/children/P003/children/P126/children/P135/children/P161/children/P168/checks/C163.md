# ReactThink llm.call payload builder check

## Summary

`P168` is solved. The builder source is mapped, the field-copy contract is explicit, and the test now contains a stale local-tool counterexample proving `llm.call` tools come from `prepare_context_result` rather than saga-local `source.tools`.

## Evidence

- Source field map: `novaic-agent-runtime/task_queue/contracts/react_think.py:98-114`.
- Prepared snapshot fields: `messages` from `prepare_context_result` at `react_think.py:107`; `tools` from `prepare_context_result` at `react_think.py:109`.
- Saga-local `source.tools` exists at `react_think.py:29` and is used for later action/retry context at `react_think.py:322` and `react_think.py:348`, not for the current provider payload builder.
- Regression pointer: `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py:34-67` now uses `stale_local_tool` on the source and asserts `prepared_tool` in the LLM call payload.
- Test run: `13 passed in 0.13s`.

## Criteria Map

- `contracts/react_think.py` mapped: satisfied.
- Fields copied from `prepare_context_result` listed: satisfied for `messages` and `tools`; metadata fields documented in result `R149`.
- Tests prove prepared source authority: satisfied by the stale-local-tool counterexample.
- Ambiguous local fallback fixed/split: no active fallback in the builder; handler/provider assembly remains sibling `P169`.

## Execution Map

- `T154` one-go executed after split from `P161`.
- Added a focused assertion to the explicit contract test.
- Recorded result `R149`.

## Stress Test

If `build_llm_call_payload` starts using `source.tools`, the new stale-local-tool assertion will fail because the expected payload contains only `prepared_tool`. If it stops copying `prepare_context_result.messages`, the existing prepared-message assertion fails.

## Residual Risk

- This check does not prove the downstream handler preserves the payload; `P169` covers that boundary.

## Result IDs

- R149
