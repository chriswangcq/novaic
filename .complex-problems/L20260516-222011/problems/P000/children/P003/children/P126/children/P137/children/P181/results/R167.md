# Active stack final context injection ordering result

## Summary

Mapped final active stack message injection. The `[Active skill stack ...]` system message is built in `novaic-common/common/contracts/llm_assembly.py` by `build_active_skill_stack_message()` and appended by pure `assemble_llm_request()` after Cortex-prepared messages and before optional no-tool warning. Runtime `handle_cortex_prepare_llm_context()` delegates to this common assembler. Provider-facing LLM calls then expand `step_ref` tool messages in `prepare_llm_call()`, and display/current projection is determined by explicit `current_round_id`, `tool_call_id`, and tool name metadata, not by whether the tool message is physically last.

## Done

- Identified final stack injection source:
  - `format_active_skill_stack_message`
  - `build_active_skill_stack_message`
  - `assemble_llm_request`
  - `assemble_llm_request_from_snapshot`
- Confirmed runtime no longer owns a local stack adapter; it calls `assemble_llm_request_from_snapshot()` from `handle_cortex_prepare_llm_context()`.
- Documented ordering:
  - Cortex read model returns base messages and stack.
  - Common LLM assembler removes any previous active-stack snapshot from base messages.
  - Common LLM assembler appends the transient active-stack system message.
  - Optional no-tool warning, if present, is appended after the stack message.
  - Runtime LLM call then expands tool step refs and applies provider multimodal processing.
- Confirmed current display projection is not positional: `expand_messages_for_llm()` chooses projection from `current_round_id`, tool-call metadata, and tool name.

## Verification

- Focused tests passed:

```bash
PYTHONPATH=novaic-common:novaic-agent-runtime:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-common/tests/test_llm_assembly_contract.py \
  novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py \
  novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py \
  novaic-agent-runtime/tests/test_runtime_explicit_contracts.py
```

Result: `40 passed in 0.15s`.

- Relevant coverage includes:
  - active stack appears as the final system message in normal prepare output,
  - runtime assembly has no local stack adapter,
  - `prepare_llm_call` injects a display image before a following system message,
  - `current_round_id` is passed to step-ref expansion.

## Known Gaps

- This ticket does not itself add new display-media tests; sibling P182 owns focused current-display regression coverage.
- No duplicate or stale final stack injection path found in this ticket.

## Artifacts

- `novaic-common/common/contracts/llm_assembly.py`
- `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py`
- `novaic-agent-runtime/task_queue/contracts/llm_call.py`
- `novaic-agent-runtime/task_queue/utils/step_result_client.py`
- `novaic-common/tests/test_llm_assembly_contract.py`
- `novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
