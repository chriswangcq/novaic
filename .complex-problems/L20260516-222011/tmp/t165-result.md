# Runtime tool wrapper ref contract mapped

## Summary

Mapped the runtime wrapper layer for tool results. This layer creates public tool content and optional durable payloads, then attaches stable `step_ref` at `handle_tool_execute`. It does not currently set a separate `payload_ref`; storage-layer code later derives `payload_ref` from `step_ref` unless a deeper externalized-payload path changes that contract.

## Source Map

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
  - `_ok(...)`: builds the public wrapper response with `content`, `tool_success`, `tool_status`, `scope_id`, `round_id`, `tool_call_id`, and `tool_name`.
  - `_tool_output_dict(...)`: normalizes structured `tool-output.v1`, display output, errors, and unstructured executor results.
  - `_display_public_output(...)`: strips image `data` from public display tool history and replaces it with placeholders.
  - `_display_durable_payload(...)`: preserves display LLM content and raw file metadata in `durable_payload`.
  - `_shell_result_output(...)`: turns shell output into bounded terminal-like text while storing full raw stdout/stderr/files in `durable_payload.raw`.
  - `handle_tool_execute(...)`: computes stable `step_ref` with `_tool_step_ref(scope_id, round_id, tool_call_id)` and attaches it to both success and error tool results.

## Contract

- Public context fields:
  - `content`: JSON string for the tool message; bounded and safe for chat/context history.
  - `tool_success` / `tool_status`: logical tool outcome, distinct from task execution success.
  - `arguments`: normalized arguments for audit/step history.
  - `step_ref`: stable step lookup identity.
- Durable/raw fields:
  - `durable_payload.version == "tool-step-payload.v1"`.
  - `durable_payload.llm_content`: exact LLM-expandable content when needed.
  - `durable_payload.raw`: raw shell/display backing data for later diagnostics or projection.
- Not owned by this layer:
  - `payload_ref` storage identity; this is assigned by Cortex/bridge persistence and is covered by child storage/read problems.

## Verification

Command:

```bash
PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py \
  novaic-agent-runtime/tests/unit/task_queue/test_tool_output_contract.py \
  novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py \
  novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py \
  novaic-agent-runtime/tests/test_runtime_explicit_contracts.py
```

Result: `39 passed in 0.16s`.

## Findings

- No code changes were needed in this leaf.
- Public display content and non-display unstructured image-like content are already sanitized.
- Shell output is terminal-like bounded text, with full raw output only in durable payload.
- This leaf confirms wrapper behavior, but storage-level `payload_ref` semantics still need the P177/P178/P179 child audits.
