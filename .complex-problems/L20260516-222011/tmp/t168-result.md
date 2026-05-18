# Externalized payload regression coverage audit result

## Summary

Audited the remaining `step_ref` / `payload_ref` ambiguity after the runtime wrapper, Cortex storage, and formatted projection contracts had been reviewed. No production code change was required in this ticket: the suspicious fallback branches are active-safe compatibility inside Cortex lookup/projection paths, and focused regression coverage already exercises the externalized-payload path from storage through formatted LLM projection.

## Done

- Reviewed runtime result handoff in `novaic-agent-runtime/task_queue/contracts/react_actions.py` and `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`.
- Reviewed Cortex lookup, payload read, event projection, writer idempotency, and payload manifest logic in:
  - `novaic-cortex/novaic_cortex/api.py`
  - `novaic-cortex/novaic_cortex/context_event_projection.py`
  - `novaic-cortex/novaic_cortex/context_event_writer.py`
  - `novaic-cortex/novaic_cortex/workspace.py`
- Classified the remaining ambiguous-looking branches:
  - `entry.get("payload_ref") == step_ref` in step lookup is safe because `step_ref` is matched first and the fallback only supports local/non-externalized or historical same-ref entries.
  - `step_ref or payload_ref` idempotency/manifest fallbacks are safe because current runtime write paths provide `step_ref`; fallback only preserves deterministic behavior for explicit payload reads or older event shapes.
  - Context event projection's `step_ref if present else payload_ref` is safe because current tool-step events carry `step_ref`, while payload-ref fallback supports explicit payload inspection and legacy event replay.
- Confirmed existing tests cover:
  - externalized payload storage and manifest indexing,
  - stable `step_ref` lookup when final `payload_ref` is a `blob://cortex-payload/...` ref,
  - no historical image injection into future LLM calls,
  - display/current/history projection split,
  - shell/tool-output manifest-only contract.

## Verification

- Cortex regression suite passed:

```bash
PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-cortex/tests/test_step_index_outcome.py \
  novaic-cortex/tests/test_context_event_api_steps_write.py \
  novaic-cortex/tests/test_context_event_projection.py \
  novaic-cortex/tests/test_payload_inspection_api.py \
  novaic-cortex/tests/test_tool_output_projection.py \
  novaic-cortex/tests/test_operational_store.py
```

Result: `80 passed in 0.55s`.

- Runtime regression suite passed:

```bash
PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py \
  novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py \
  novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py \
  novaic-agent-runtime/tests/unit/task_queue/test_tool_output_contract.py \
  novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py \
  novaic-agent-runtime/tests/test_runtime_explicit_contracts.py \
  novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py
```

Result: `62 passed in 0.19s`.

## Known Gaps

- No production gap found in this ticket.
- The branch names still read like compatibility code; they should be watched if the project later chooses to delete all historical replay support, but removing them now would break explicit payload-ref lookup and older event replay without improving the current externalized-payload contract.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/novaic_cortex/context_event_projection.py`
- `novaic-cortex/novaic_cortex/context_event_writer.py`
- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-agent-runtime/task_queue/contracts/react_actions.py`
- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
- `novaic-agent-runtime/task_queue/utils/step_result_client.py`
