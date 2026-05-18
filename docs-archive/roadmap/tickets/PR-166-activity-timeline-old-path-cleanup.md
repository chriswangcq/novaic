# PR-166 — Activity Timeline Projection and Old Path Cleanup

> Historical note: superseded by PR-193. The bridge path described below no longer exists as a product path; current Agent Monitor data is `agent-activity-records` / `agent-activity-participants`.

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
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

## Small Tickets

- [PR-166A — Activity Timeline projection contract](PR-166A-activity-timeline-projection-contract.md).
- [PR-166B — App monitor renders product-level observation/reasoning/action](PR-166B-app-monitor-activity-phase-rendering.md).
- [PR-166C — Remove backend `log-payloads` diagnostic payload path](PR-166C-remove-backend-log-payloads-diagnostic-path.md).

## Current-State Analysis

2026-05-02 scan after PR-165 found:

1. PR-166A tightened Cortex `POST /v1/trace/project` into a user-facing Activity Timeline projection contract. Records expose only `order`, `phase`, `kind`, `title`, `text`, `truncated`, optional `tool`, optional `status`, and optional `has_payload`; debug fields such as `source`, `tool_call_id`, `arguments_preview`, `payload_ref`, and per-record `scope_path` are no longer default output.
2. The App monitor currently renders the Entangled `execution-logs` stream through `useLogs` and `ExecutionLog`. Existing tests already guard against normal display of Factory ids, `result_id`, raw MCP content, `Input Parameters`, `Execution Result`, and technical labels.
3. Common owns semantic display contracts for the current monitor path: `execution_log_display.json` and `tool_product_semantics.json`.
4. PR-166C retired the stale backend diagnostic branch: `log-payloads` is no longer registered in Common/Business schema, Business no longer exposes `log-payloads.get_payload`, `/internal/logs/broadcast` no longer writes raw `input` / `result` / `error`, and Runtime no longer sends `input_data` / `result_data` to the monitor broadcast API.
5. `execution-logs` still has product value as the lightweight realtime monitor stream until the App switches to a Cortex trace projection. The cleanup target is the old payload drilldown branch, not the lightweight stream itself.

## Current Iteration

PR-166A, PR-166B, and PR-166C are deployed and closed. The current implementation keeps `execution-logs` as the realtime App monitor stream, adds explicit observation/reasoning/action/summary phase rendering in the App, and keeps Cortex `trace/project` as the stricter projection contract for trace-backed views.

## Closure

Closed 2026-05-02 after all small tickets were implemented, tested, deployed, and pushed.

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
