# PR-164C — Reasoning and Action Trace Projection

> Historical note: superseded for user-facing Agent Monitor delivery by PR-193. Cortex no longer exposes `/v1/trace/project`; Runtime now materializes Entangled activity projection rows during execution.

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-agent-runtime`, `novaic-cortex`, `novaic-app`, docs |
| Parent | [PR-164](PR-164-cortex-observation-payload-integration.md) |
| Theme | Observation / reasoning / action projection |

## Goal

Make Cortex expose a coherent work trace that can project user-visible Activity Timeline phases: Observation, Reasoning, and Action.

`reasoning_content` should be preserved as the LLM's own reasoning trace where available. There should be no model-generated monitor-only reasoning summary.

## Current-State Analysis

Completed 2026-05-02 after PR-164B.

Starting state:

- Runtime already preserved provider-authored `reasoning_content` inside assistant context messages.
- Assistant `tool_calls` represented actions, while PR-164A/PR-164B tool result percepts lived in Cortex `steps/`.
- Cortex did not expose a first-class projection API that separated reasoning/action/observation for a user-facing monitor.
- App display contract had a small gap for the new `payload_inspected` display kind.

## Implementation Tasks

- [x] Define Cortex trace projection records for observation, reasoning, action, and summary.
- [x] Project assistant `reasoning_content` into reasoning records without generating new summaries.
- [x] Project tool calls as actions and PR-164A tool result percepts as observations.
- [x] Keep developer diagnostics separate from the normal Activity Timeline surface.
- [x] Align App monitor display contract with `payload_inspected`.

## Tests

- [x] Unit: trace projection separates observation/reasoning/action.
- [x] Unit: reasoning content is preserved when present and absent when provider omitted it.
- [x] Route test: `/v1/trace/project` accepts JSON body and returns projected records.
- [x] App unit: normal monitor does not display raw result ids and renders payload inspection semantically.

Test evidence:

- `novaic-cortex`: `PYTHONPATH=.:../novaic-common pytest -q` -> 395 passed, 16 skipped.
- `novaic-app`: `npm run test:unit` -> 42 passed.
- `novaic-app`: `npm run build` -> passed with existing Vite chunk warnings.

## Smoke / Deploy / Git

- [x] Run cortex/app tests.
- [x] Deploy services and frontend.
- [x] Production smoke: Cortex trace projection returns observation/reasoning/action without raw payload leakage.
- [x] Commit touched repos.

Commit evidence:

- `novaic-cortex`: `c7349b4 feat(cortex): project activity trace phases`
- `novaic-app`: `3887182 fix(app): render payload inspection monitor events`

## Done Criteria

- [x] User-facing Agent Monitor can be driven from the Cortex projection.
- [x] Reasoning is source-authored `reasoning_content`, not an extra generated summary.
- [x] Debug payloads remain outside the normal monitor projection.
