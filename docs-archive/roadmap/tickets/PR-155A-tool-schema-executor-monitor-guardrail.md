# PR-155A — Add Tool Schema / Executor / Monitor Contract Guardrail

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-155 |
| Repos | novaic-agent-runtime, docs |

## Goal

Add a runtime-side invariant test proving every Common LLM-facing builtin tool has a Runtime executor and Agent Monitor display mapping, with no extra legacy executors.

## Why This Matters

Tool schema is the LLM-facing promise. The system should fail tests immediately if a tool is exposed without an executor, if an executor exists for a deleted tool, or if the monitor has no semantic display mapping for a tool.

## Implementation Plan

1. [x] Add runtime guardrail comparing Common `AGENT_BUILTIN_TOOL_SCHEMAS` names to Runtime `_EXECUTORS`.
2. [x] Extend the same guardrail to compare Agent Monitor `tool_display_kinds` keys.
3. [x] Run targeted Runtime/Common/Cortex tool contract tests.
4. [x] Deploy Runtime if tests pass.
5. [ ] Commit Runtime and parent docs/submodule.

## Unit / Guardrail Tests

- [x] Runtime tool path contract tests pass.
- [x] Runtime execution-log metadata tests pass.
- [x] Common tool definition contract tests pass.
- [x] Cortex tool schema limits tests pass.

## Smoke / Deploy / Git

- [x] Deploy Runtime.
- [x] `./deploy status` healthy.
- [x] Commit Runtime.
- [ ] Parent repo submodule/docs commit and push.

## Evidence

- `novaic-agent-runtime`: `python3 -m pytest tests/test_runtime_tool_path_contract.py tests/test_pr86_execution_log_metadata.py tests/unit/task_queue/test_tool_handlers_display_chat_history.py -q` — 20 passed.
- `novaic-common`: `python3 -m pytest tests/test_tool_definitions_contract.py tests/test_execution_log_display_contract.py -q` — 9 passed.
- `novaic-cortex`: `python3 -m pytest tests/test_tool_schemas_limits.py -q` — 10 passed.
- `./deploy runtime` — deployed Runtime and restarted backends.
- `./deploy status` — API services healthy; Relay running.
- `novaic-agent-runtime` commit `87c3865` — `runtime: guard tool schema executor alignment`.
