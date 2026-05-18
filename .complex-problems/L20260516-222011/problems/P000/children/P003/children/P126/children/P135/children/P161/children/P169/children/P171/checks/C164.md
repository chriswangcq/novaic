# LLMCall contract provider payload source check

## Summary

`P171` is solved. The pure contract layer uses explicit `LLMCallInput` fields for messages/tools and injected preprocessing functions for message transformation. The one-go result is accepted because it added the missing tools assertion and ran the focused contract suite.

## Evidence

- `LLMCallInput.from_payload`: `novaic-agent-runtime/task_queue/contracts/llm_call.py:37`.
- Explicit messages source: payload `messages` required and deep-copied at `llm_call.py:44-55`.
- Explicit tools source: payload `tools` type-checked and deep-copied at `llm_call.py:49-57`.
- Provider message preprocessing dependencies are function parameters at `llm_call.py:120-122` and called in order at `llm_call.py:128-137`.
- Provider output fields are returned at `llm_call.py:138-145`, including `messages=processed` and `tools=deepcopy(source.tools)`.
- Regression pointer: `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py:100-142`.
- Test run: `13 passed in 0.14s`.

## Criteria Map

- `LLMCallInput.from_payload` and `prepare_llm_call` mapped: satisfied.
- Explicit source of messages/tools documented: satisfied.
- Tests prove preprocessing injected and ordered: satisfied by call-order assertions and source guard that business transport does not own sanitization/multimodal preprocessing.
- Hidden source of context/messages/tools fixed or split: no hidden source found in contract layer; handler delegation remains sibling `P172`.

## Execution Map

- `T156` one-go executed after `P169` split.
- Added a missing `prepared.tools` assertion.
- Recorded result `R150`.

## Stress Test

If the contract stops passing payload tools to provider calls, the new `prepared.tools` assertion fails. If preprocessing moves back into the business transport or handler bypasses the explicit contract, existing static guards in `test_runtime_explicit_contracts.py` fail.

## Residual Risk

- Handler-level direct context reads are not proven by this leaf; `P172` covers that boundary.

## Result IDs

- R150
