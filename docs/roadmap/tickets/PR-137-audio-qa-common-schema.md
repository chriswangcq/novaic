# PR-137: Expose `audio_qa` from the common LLM tool schema

## Status

`[deployed]`

## Background

PR-132 intentionally quarantined `audio_qa` because Runtime did not have an executor. Once PR-136 restores the executor, the common LLM schema can expose `audio_qa` again from the canonical schema source.

## Scope

- Add `audio_qa` to `common.tools.llm_builtin.AGENT_BUILTIN_TOOL_SCHEMAS`.
- Include `audio_qa` in `MULTIMODAL_TOOLS` via `input_schema_tools(...)`.
- Replace the quarantine guardrail with a positive contract test.
- Add or update execution-log display contract mapping if needed so Agent Monitor has a semantic display kind for audio analysis.

## Non-goals

- Do not duplicate tool schema in `definitions.py`.
- Do not reintroduce old manual `MULTIMODAL_TOOLS` schema.
- Do not touch Runtime executor logic; PR-136 owns execution.

## Unit Tests

- Common canonical schema includes `audio_qa`.
- `MULTIMODAL_TOOLS["audio_qa"]` is adapted from canonical schema.
- Active builtin tool names include `audio_qa`.
- Tool schema remains OpenAI-compatible (`parameters`) and metadata-compatible (`inputSchema`) through the existing adapter.

## Smoke Test

- Local schema smoke prints active tool names and verifies `audio_qa` is present.
- After deploy, query `/v1/internal/tools` and confirm `audio_qa` appears in LLM tools.

## Deployment Checklist

- [x] Unit tests pass locally.
  - `cd novaic-common && python -m pytest tests/test_tool_definitions_contract.py tests/test_execution_log_display_contract.py -q`
  - `cd novaic-cortex && python -m pytest tests/test_tool_schemas_limits.py -q`
- [x] Commit Common changes.
  - `2017e1a feat(tools): expose audio qa schema`
- [x] Push Common branch.
- [x] Deploy Common/Cortex tool schema consumer if required by deployment packaging.
  - Deployed as part of `./deploy services` on 2026-05-01.
- [x] Production smoke: active LLM tool list includes `audio_qa`.
  - Queried Cortex `/v1/internal/tools`; returned `audio_qa` between `display` and `chat_history`.
- [x] Update this ticket and parent submodule pointer.

## Implementation Notes

- Cortex exact tool-name guardrail was updated explicitly:
  - `c52c1af test(cortex): accept audio qa builtin tool`

## GitHub / Merge

- Depends on PR-136 being merged/deployed.
- Suggested commit message: `feat(tools): expose audio qa schema`
