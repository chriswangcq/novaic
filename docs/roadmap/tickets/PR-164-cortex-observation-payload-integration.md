# PR-164 — Cortex Observation and Payload Integration

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-cortex`, `novaic-agent-runtime`, `novaic-business`, `novaic-common`, docs |
| Depends on | PR-163 |
| Theme | Work trajectory / perception record |

## Goal

Make Cortex the durable work trajectory for agent perception/action: observation percepts, LLM reasoning, tool actions, replies, interpretations, and scope summaries.

Large or sensitive tool results should not be blindly embedded into Cortex. They should become observation summaries plus payload refs; the agent can inspect tails/heads or request explicit interpretation when useful.

## Required Process

1. Analyze current Cortex event/scope/result model and runtime write sites.
2. Create small tickets for observation, payload ref, and interpretation slices.
3. Implement one small ticket at a time.
4. For each small ticket: unit tests, smoke test, deploy plan/result, Git commit/merge evidence.
5. Confirm Activity Timeline can project user-visible work without raw debug payloads.

## Planned Small Tickets

- PR-164A — Cortex observation percept contract and write path.
- PR-164B — Payload ref contract and inspection tool integration.
- PR-164C — Reasoning/action/reply projection consistency.

## Current-State Analysis

Pending after PR-163.

## Boundary Invariants

- Cortex owns work trajectory, not external domain truth.
- Raw tool payload is stored by the responsible domain and referenced from Cortex.
- Summary happens only when explicitly requested by the agent or by a deterministic display budget, not as hidden memory inference.
- `summary.md` remains scope-close summary, not a second memory channel.

## Done Criteria

- Observation writes are covered by tests.
- Payload refs are resolvable, bounded, and safe to display.
- Reasoning content is preserved where available and separated from generated summaries.
- No raw MCP/HTTP/debug blobs leak into normal Agent Monitor.

