# Map Cortex prepare handler response shape

## Problem Definition

`handle_cortex_prepare_llm_context` performs notification hint ingestion, calls Cortex prepare, loads tools, and assembles the snapshot returned to the saga. We need source evidence and tests proving this handler does not use local continuity as provider-message authority.

## Proposed Solution

Inspect the handler source, the input/output contract types it uses, and existing tests around prepare context. Classify `handle_context_read` as notification-hint ingestion rather than LLM context authority, map `CortexPreparedContext.from_mapping`, tool schema loading, warning/stack injection, and `assembly_output.to_dict()`. Add a focused guard only if returned fields are not covered.

## Acceptance Criteria

- Handler source pointers cover payload parsing, `handle_context_read`, `bridge.prepare_for_llm`, `CortexPreparedContext.from_mapping`, `load_tool_schemas`, assembly call, and returned fields.
- `handle_context_read` inside this handler is classified as active-safe or stale with justification.
- Existing tests around prepared messages/tools/warnings are identified and run.
- If returned messages/tools can come from `read_result.context`, a guard/fix is added or a blocking child is spawned.

## Verification Plan

- Inspect `cortex_handlers.py` and relevant contract module source.
- Run `test_pr85_llm_context_smoke_guardrails.py`, `test_no_tool_warning.py`, `test_pr67_wake_child_scope.py`, and `test_runtime_explicit_contracts.py`.

## Risks

- `handle_context_read` is deliberately called before prepare; misclassifying it could hide a regression. The result must state what fields from `read_result` enter assembly.

## Assumptions

- `assemble_llm_request_from_snapshot` is the pure boundary for combining the prepared snapshot, transient new messages, tools, and warning.
