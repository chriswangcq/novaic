# PR-166 — Activity Timeline Projection and Old Path Cleanup

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-app`, `novaic-business`, `novaic-agent-runtime`, `novaic-cortex`, docs |
| Depends on | PR-165 |
| Theme | User-facing monitor / entropy cleanup |

## Goal

Project a coherent Agent Monitor from Cortex and Environment without exposing debug-only transport details to normal users.

The monitor should show the agent's observation, reasoning, and action at product level. Old execution-log, result-id, raw MCP content, hidden report, and fallback diagnostic paths must be physically removed or moved behind explicit developer diagnostics if still valuable.

## Required Process

1. Analyze current App monitor, execution log display, message status, Entangled entities, and backend projection APIs.
2. Create small tickets for timeline projection, UI display, and old-path deletion.
3. Implement one small ticket at a time.
4. For each small ticket: unit tests, smoke test, deploy plan/result, Git commit/merge evidence.
5. Confirm user-facing and developer-facing surfaces are separated before closing.

## Planned Small Tickets

- PR-166A — Activity Timeline projection contract.
- PR-166B — App monitor renders product-level observation/reasoning/action.
- PR-166C — Physical deletion of old diagnostic/fallback projection paths.

## Current-State Analysis

Pending after PR-165.

## Boundary Invariants

- Agent Monitor is a product surface, not a raw diagnostic panel.
- Developer diagnostics must not be the default user view.
- Message status remains delivery/read UI state, not agent-loop state.
- Old projection paths must not remain as silent fallback branches.

## Done Criteria

- Normal monitor shows useful work events without result ids/raw payloads.
- Expanded view stays product-level unless an explicit developer surface is chosen.
- Guardrails catch old execution-log/fallback reintroduction.
- Deployment and smoke evidence are recorded.

