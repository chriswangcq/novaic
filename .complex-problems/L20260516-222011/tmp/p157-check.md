# Runtime LLM prepare caller authority success check

## Summary

`P157` is solved by `R136`. The runtime provider-message path is now evidenced and guarded: ReAct think builds `llm.call` input from the previous `prepare_context` step result, the prepare handler uses Cortex `prepare_for_llm` for the context snapshot, and the final LLM call handler has a source guard preventing direct `context.read`/`read_context` authority.

## Evidence

- Runtime path evidence:
  - `novaic-agent-runtime/task_queue/sagas/react_think.py:149` registers `prepare_context` before `call_llm`.
  - `novaic-agent-runtime/task_queue/sagas/react_think.py:52` passes `prev_result` into `build_llm_call_payload`.
  - `novaic-agent-runtime/task_queue/contracts/react_think.py:98` builds `messages` and `tools` from `prepare_context_result`.
  - `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py:325` calls `bridge.prepare_for_llm(agent_root_scope_id)`.
  - `novaic-agent-runtime/task_queue/handlers/llm_handlers.py:120` delegates final provider request shaping to `prepare_llm_call`.
- Guard evidence:
  - `test_prepare_llm_context_uses_prepare_snapshot_not_context_read_projection` creates a conflicting legacy `context.read` projection and prepared snapshot, then proves only the prepared snapshot appears in final LLM messages.
  - `test_llm_call_handler_does_not_read_cortex_context_as_authority` prevents the final LLM handler from reading Cortex context directly.
- Verification commands:
  - `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py novaic-agent-runtime/tests/test_runtime_explicit_contracts.py` passed with `20 passed`.
  - `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/test_no_tool_warning.py novaic-agent-runtime/tests/test_pr67_wake_child_scope.py` passed with `10 passed`.

## Criteria Map

- Runtime prepare-context caller and LLM assembly path are mapped: satisfied by the source pointers from `react_think`, `cortex_handlers`, `react_think` contracts, and `llm_handlers`.
- Evidence proves runtime uses `/v1/context/prepare_for_llm` or explicit prepare contract: satisfied by `CortexBridge.prepare_for_llm` invocation through `handle_cortex_prepare_llm_context` and tests asserting the prepared snapshot is authoritative.
- Evidence proves runtime LLM assembly does not call `read_context` as authority: satisfied by the new source guard and conflicting-snapshot test.

## Execution Map

- Result `R136` made one code/doc cleanup and two guardrail test additions.
- No split/spawn children were required because no active authoritative legacy LLM assembly path was found.
- Verification covered both the prepare handler and final LLM call handler.

## Stress Test

- The strongest plausible failure mode is `context.read` returning stale/legacy projection messages while `prepare_for_llm` returns the correct read-model snapshot. The added test injects exactly that conflict and asserts only the prepared snapshot reaches final messages.
- A second plausible failure mode is someone adding direct `read_context` usage to `llm_handlers`; the source guard catches that.

## Residual Risk

- `context.read` still exists as an active topic for notification-hint insertion and idempotency scanning. That naming is confusing, but this check treats it as non-blocking because the added conflict test proves it is not provider-message authority.
- Some older tests still configure `bridge.read_context.return_value`; this can be cleaned later for clarity, but current guards prevent it from masking the LLM authority path.

## Result IDs

- R136
