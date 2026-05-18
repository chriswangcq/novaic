# PR-170C — Payload Interpretation Runtime Executors

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-agent-runtime`, docs |
| Parent | PR-170 |

## Goal

Wire `payload_summarize` and `payload_qa` LLM tool calls to Runtime executors that call Cortex interpretation endpoints.

## Current-State Analysis

Runtime has executors and bridge methods for `payload_read` / `payload_search` only. Tool result writing already records explicit tool results as Cortex observations, so interpretation results can reuse that path once executors exist.

## Implementation Checklist

- [x] Add bridge methods for summarize/QA endpoints.
- [x] Add Runtime executors with validation and bounded args.
- [x] Fetch agent LLM config for interpretation calls.
- [x] Add display summaries for monitor semantics.
- [x] Update runtime tool path contract tests.
- [x] Run Runtime tests.
- [x] Commit and push Runtime changes; update parent submodule pointer.

## Closure Notes

- Added `payload_summarize` and `payload_qa` Runtime executors.
- Added `CortexBridge.payload_summarize(...)` and `CortexBridge.payload_qa(...)`.
- Runtime now resolves the default agent LLM config via Business `/internal/config/llm/agent/{agent_id}` and passes model/factory fields to Cortex interpretation endpoints.
- Budgets are clamped in Runtime before crossing the Cortex boundary.
- Monitor summaries are bounded user-facing text, not raw payload/debug output.

## Verification

- `PYTHONPATH=.:../novaic-common pytest -q tests/unit/task_queue/test_payload_tool_handlers.py tests/test_runtime_tool_path_contract.py`
- `python -m py_compile task_queue/handlers/tool_handlers.py task_queue/utils/cortex_bridge.py`
- `PYTHONPATH=.:../novaic-common pytest -q`

## Done Criteria

- Explicit interpretation tool calls execute and become normal Cortex tool observations.
- Missing config, payload refs, or questions fail visibly and boundedly.
