# PR-164B — Explicit Payload Inspection Tools

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-common`, `novaic-agent-runtime`, `novaic-cortex`, docs |
| Parent | [PR-164](PR-164-cortex-observation-payload-integration.md) |
| Theme | Explicit observation / payload inspection |

## Goal

Expose explicit payload inspection actions for payload refs: read ranges, search, and bounded previews. The agent should inspect payloads like a human inspecting terminal/file output, not receive hidden automatic summaries.

## Current-State Analysis

Pending PR-164A. The expected starting point is that Cortex steps carry `payload_ref` and safe observation percepts, while raw payload bodies live behind payload records.

## Implementation Tasks

- Define canonical payload inspection schemas in `novaic-common`.
- Implement Runtime executors that call Cortex payload inspection APIs.
- Add Cortex payload read/preview/search endpoints with deterministic budgets.
- Ensure every payload inspection result is itself written back as a new observation step.

## Tests

- Unit: schema/executor/display contract alignment.
- Unit: payload read respects range and budget.
- Unit: payload search returns bounded matches and redacts unsupported binary payloads.
- Smoke: shell long output can be inspected by payload ref without injecting the full payload.

## Smoke / Deploy / Git

- Run common/runtime/cortex tests.
- Deploy services.
- Production smoke with a long shell output and explicit payload inspection.
- Commit touched repos and root submodule/docs update.

## Done Criteria

- Agent has explicit tools for payload inspection.
- No Runtime auto-summary is introduced.
- Payload inspection outputs are bounded observations, not raw debug dumps.

