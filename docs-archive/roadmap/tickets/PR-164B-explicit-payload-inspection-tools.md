# PR-164B — Explicit Payload Inspection Tools

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-common`, `novaic-agent-runtime`, `novaic-cortex`, docs |
| Parent | [PR-164](PR-164-cortex-observation-payload-integration.md) |
| Theme | Explicit observation / payload inspection |

## Goal

Expose explicit payload inspection actions for payload refs: read bounded ranges and search bounded match contexts. The agent should inspect payloads like a human inspecting terminal/file output, not receive hidden automatic summaries.

## Current-State Analysis

Completed 2026-05-02 after PR-164A.

Starting state:

- Cortex steps carried safe `observation` percepts plus `payload_ref`.
- Raw tool payloads lived in scope-local `payloads/` records.
- Runtime and Cortex still lacked LLM-visible actions for inspecting those payload refs explicitly.

Decision: implement only deterministic inspection tools in this slice: `payload_read` and `payload_search`. Do not introduce `payload_summarize` / `payload_qa` yet, because those would require a separate interpretation model path and must not become hidden auto-summary.

## Implementation Tasks

- [x] Define canonical payload inspection schemas in `novaic-common`.
- [x] Implement Runtime executors that call Cortex payload inspection APIs.
- [x] Add Cortex payload read/search endpoints with deterministic budgets.
- [x] Ensure every payload inspection result is itself written back as a new observation step via the existing tool result path.

## Tests

- [x] Unit: schema/executor/display contract alignment.
- [x] Unit: payload read respects range and budget.
- [x] Unit: payload search returns bounded matches.
- [x] Smoke: shell long output can be inspected by payload ref without injecting the full payload.

Test evidence:

- `novaic-common`: `PYTHONPATH=.:../novaic-agent-runtime pytest -q` -> 119 passed.
- `novaic-agent-runtime`: `PYTHONPATH=.:../novaic-common pytest -q` -> 207 passed.
- `novaic-cortex`: `PYTHONPATH=.:../novaic-common pytest -q` -> 391 passed, 16 skipped.

## Smoke / Deploy / Git

- [x] Run common/runtime/cortex tests.
- [x] Deploy services via `./deploy services`.
- [x] Production smoke with a long shell output and explicit payload inspection.
- [x] Commit touched repos.

Commit evidence:

- `novaic-common`: `2cdffba feat(common): add payload inspection tools`
- `novaic-agent-runtime`: `fc18d7c feat(runtime): execute payload inspection tools`
- `novaic-cortex`: `60fe590 feat(cortex): add payload inspection endpoints`

Production smoke evidence:

- `payload_read_ok=True`
- `payload_search_ok=True`
- `has_payload_tools=True`
- active tool count: 12

## Done Criteria

- [x] Agent has explicit tools for payload inspection.
- [x] No Runtime auto-summary is introduced.
- [x] Payload inspection outputs are bounded observations, not raw debug dumps.
