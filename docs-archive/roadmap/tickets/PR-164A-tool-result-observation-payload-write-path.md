# PR-164A — Tool Result Observation Payload Write Path

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-common`, `novaic-agent-runtime`, `novaic-cortex`, docs |
| Parent | [PR-164](PR-164-cortex-observation-payload-integration.md) |
| Theme | Cortex work trajectory / payload ref |

## Goal

Make every Runtime-written tool result step store a bounded observation percept plus `payload_ref`, not raw result body in the Cortex step JSON.

The raw tool result payload must be stored behind a Cortex payload record so existing LLM tool-result replay can resolve it by `result_id` without leaking raw payloads into the default scope trace.

## Current-State Analysis

- Runtime writes `step.result = content` in `react_actions._build_save_results_tasks`.
- Cortex stores that raw `result` inside `steps/*.json`.
- `steps/read_formatted` reads `step.result` and formats it for LLM replay.
- Agent Monitor does not need raw `result`; it already receives semantic execution metadata from Runtime.

## Implementation Tasks

- Add a shared observation/percept builder for tool results.
- Change Runtime step writes to include `observation`, `payload_ref`, and a write-time `payload`, with no `result` field.
- Change Cortex `write_step` to externalize `payload` into a payload record and reject inline `result` for new tool steps.
- Change Cortex `read_formatted` / `read_preview` to resolve through `payload_ref` and use the observation preview where appropriate.
- Update tests that previously expected raw `step.result`.

## Tests

- Unit: common observation builder covers small output, long output, structured MCP content, and no raw long payload leak.
- Unit: Runtime tool-result save step has `observation`/`payload_ref`/`payload` and no `result`.
- Unit: Cortex step write externalizes payload, rejects inline result, and resolves payload by ref for formatted reads.
- Regression: Context DFS still preserves `result_id` for tool result replay.

## Smoke / Deploy / Git

- Run relevant `pytest` suites for `novaic-common`, `novaic-agent-runtime`, and `novaic-cortex`.
- Deploy services with `./deploy services`.
- Production smoke: confirm active tool schemas still load and old direct communication tools remain absent.
- Commit each touched repo and update the root submodule/docs commit.

## Done Criteria

- [x] New tool result steps no longer contain raw `result`.
- [x] LLM tool result replay still resolves via `result_id` / `payload_ref`.
- [x] Observation percept is bounded and safe by construction.
- [x] No compatibility branch keeps the old raw-result write path alive; Cortex rejects inline `result` for new tool steps.

## Implementation Notes

Completed 2026-05-02.

- `novaic-common` commit `97f2a94` adds `common.contracts.cortex_observation.build_tool_observation` and unit coverage.
- `novaic-agent-runtime` commit `05a3149` changes Runtime tool-result step writes to `observation + payload + payload_ref + result_id`, with no `result` field.
- `novaic-cortex` commit `351ee68` externalizes step payloads into scope-local `payloads/`, makes `read_formatted` resolve via `payload_ref`, and rejects inline `result` on new tool steps.

## Verification

- `novaic-common`: `PYTHONPATH=.:../novaic-agent-runtime pytest -q` → 117 passed.
- `novaic-agent-runtime`: `PYTHONPATH=.:../novaic-common pytest -q` → 203 passed.
- `novaic-cortex`: `PYTHONPATH=.:../novaic-common pytest -q` → 388 passed, 16 skipped.
- Deploy: `./deploy services` → all backend services healthy on ports 19900/19999/19998/19993/19997/19995/19996.
- Production smoke: active tool schemas/executors match and old `chat_reply` / `chat_history` / `subagent_send` are absent.
- Production smoke: Cortex `Workspace.write_step` stores no `result` or inline `payload`, resolves `payload_ref`, and rejects inline `result` with `ValueError`.
