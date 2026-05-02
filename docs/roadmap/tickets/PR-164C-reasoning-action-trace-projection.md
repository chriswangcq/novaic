# PR-164C — Reasoning and Action Trace Projection

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-agent-runtime`, `novaic-cortex`, `novaic-app`, docs |
| Parent | [PR-164](PR-164-cortex-observation-payload-integration.md) |
| Theme | Observation / reasoning / action projection |

## Goal

Make Cortex expose a coherent work trace that can project user-visible Activity Timeline phases: Observation, Reasoning, and Action.

`reasoning_content` should be preserved as the LLM's own reasoning trace where available. There should be no model-generated monitor-only reasoning summary.

## Current-State Analysis

Runtime already preserves `reasoning_content` inside assistant messages and sends a preview to execution-log metadata. Cortex does not yet expose a first-class projection API that separates reasoning/action/observation for the user-facing monitor.

## Implementation Tasks

- Define Cortex trace projection records for observation, reasoning, action, and summary.
- Project assistant `reasoning_content` into reasoning records without generating new summaries.
- Project tool calls as actions and PR-164A tool result percepts as observations.
- Keep developer diagnostics separate from the normal Activity Timeline surface.

## Tests

- Unit: trace projection separates observation/reasoning/action.
- Unit: reasoning content is preserved when present and absent when provider omitted it.
- App unit: normal monitor does not display raw result ids, raw MCP content, or HTTP payloads.

## Smoke / Deploy / Git

- Run cortex/runtime/app tests.
- Deploy services and frontend.
- Production smoke: a simple turn displays meaningful observation/reasoning/action without debug payloads.
- Commit touched repos and root submodule/docs update.

## Done Criteria

- User-facing Agent Monitor can be driven from the Cortex projection.
- Reasoning is source-authored `reasoning_content`, not an extra generated summary.
- Debug payloads remain outside the normal monitor.

