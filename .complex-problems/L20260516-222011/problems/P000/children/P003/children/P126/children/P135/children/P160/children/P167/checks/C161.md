# CortexBridge prepare_for_llm endpoint contract check

## Summary

`P167` is solved. The bridge method is mapped to the correct Cortex prepare endpoint, its explicit tenant payload is now guarded by a regression test, and no active prepare path fallback to `read_context` was found. The one-go shortcut is acceptable because the work narrowed to one client method and one direct contract test with targeted verification.

## Evidence

- Implementation pointer: `novaic-agent-runtime/task_queue/utils/cortex_bridge.py:474` defines `prepare_for_llm`.
- Endpoint and payload pointer: `novaic-agent-runtime/task_queue/utils/cortex_bridge.py:482` posts to `/v1/context/prepare_for_llm` with `{**self._tenant(), "scope_id": scope_id}`.
- Separate projection endpoint pointer: `novaic-agent-runtime/task_queue/utils/cortex_bridge.py:143` defines `read_context`, and `novaic-agent-runtime/task_queue/utils/cortex_bridge.py:148` posts to `/v1/context/read`; this is not called by `prepare_for_llm`.
- Regression pointer: `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py:304` asserts path, payload, and passthrough return identity for `prepare_for_llm`.
- Focused test run: `26 passed in 0.16s` for `test_runtime_explicit_contracts.py`, `test_pr85_llm_context_smoke_guardrails.py`, and `test_pr67_wake_child_scope.py`.

## Criteria Map

- `cortex_bridge.py` `prepare_for_llm` line pointers: satisfied by `cortex_bridge.py:474` and `cortex_bridge.py:482`.
- Return/passthrough shape documented: satisfied by the docstring return shape at `cortex_bridge.py:480` and regression `assert result is prepared` at `test_runtime_explicit_contracts.py:322`.
- Fallback to `read_context` classified/fixed: satisfied by search evidence showing prepare handler uses `bridge.prepare_for_llm(...)`; `read_context` remains in separate context-read paths, not the LLM prepare path.
- Focused tests identified/run: satisfied by the targeted pytest command and `26 passed`.

## Execution Map

- Created ticket `T152`.
- Executed a direct bridge audit and added one regression test.
- Recorded result `R147`.

## Stress Test

The new test monkeypatches `_post` and would fail if `prepare_for_llm` changes to `/v1/context/read`, drops tenant fields, changes the `scope_id`, or transforms the returned prepared payload instead of passing it through. The search also checked that handler usage points at `bridge.prepare_for_llm(...)` rather than `read_context`.

## Residual Risk

- Broader runtime LLM payload handoff and historical context-read residue are intentionally outside this leaf and remain covered by sibling problems `P161` and `P162`.
- This check does not claim the Cortex service implementation itself is correct; `P166` covered the runtime handler response shape and sibling Cortex/runtime problems continue the broader audit.

## Result IDs

- R147
