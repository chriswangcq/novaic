# Cortex prepare handler response shape map result

## Summary

Mapped `handle_cortex_prepare_llm_context` and its assembly boundary. The handler uses `handle_context_read` only to ingest current Environment notification hints and pass `new_messages`; final provider messages are built from `CortexPreparedContext.from_mapping(bridge.prepare_for_llm(...))`, tool schemas, active stack snapshot, and optional no-tool warning through `assemble_llm_request_from_snapshot`.

## Done

- Mapped payload parsing: `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py:296-299` uses `LLMPrepareContextInput.from_mapping`.
- Mapped notification hint ingestion: `cortex_handlers.py:301-313` calls `handle_context_read(...)`; if it fails, the handler returns that failure. Its `read_result.get("new_messages", [])` is passed to assembly, but `read_result.context` is not used.
- Mapped authoritative prepare call: `cortex_handlers.py:320-329` calls `bridge.prepare_for_llm(prepare_input.agent_root_scope_id)` and validates with `CortexPreparedContext.from_mapping`.
- Mapped tool schema load: `cortex_handlers.py:331-335` calls `bridge.load_tool_schemas(subagent_id=...)`.
- Mapped warning and stack assembly: `cortex_handlers.py:337-356` builds `LLMContextAssemblySnapshot(...)`, calls `assemble_llm_request_from_snapshot(...)`, and returns `assembly_output.to_dict()`.
- Mapped output shape: `novaic-common/common/contracts/llm_assembly.py:115-139` returns `success`, `scope_id`, `agent_root_scope_id`, `wake_scope_path`, `context`, `messages`, `tools`, `tool_names`, `new_messages`, and `stack`.
- Mapped pure assembly: `llm_assembly.py:233-273` copies messages from `cortex_context.messages`, appends active stack and optional warning, adapts tools, and carries `new_messages` separately.
- Classified `handle_context_read` as active-safe for notification hints: it may affect `new_messages`, but guard tests prove `read_result.context` does not become provider-message authority.

## Verification

- Ran `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py novaic-agent-runtime/tests/test_no_tool_warning.py novaic-agent-runtime/tests/test_pr67_wake_child_scope.py novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`.
- Result: `31 passed`.
- Existing guard evidence includes `test_prepare_llm_context_uses_prepare_snapshot_not_context_read_projection` and `test_prepare_llm_context_static_authority_contract`.

## Known Gaps

- None for handler response shape. The bridge endpoint contract is owned by sibling `P167`.

## Artifacts

- `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py`
- `novaic-common/common/contracts/llm_assembly.py`
- `novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py`
- `novaic-agent-runtime/tests/test_no_tool_warning.py`
- `novaic-agent-runtime/tests/test_pr67_wake_child_scope.py`
- `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`
