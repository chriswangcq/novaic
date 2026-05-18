# PR-169 — App Cortex Activity Timeline Cutover

> Superseded by PR-193 (2026-05-03). The historical `agents.activity_timeline -> Cortex /v1/trace/project` path described below has been physically removed; current Agent Monitor data comes from Entangled `agent-activity-records` / `agent-activity-participants`.

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-app`, `novaic-cortex`, docs |
| Depends on | PR-166, PR-168 preferred |
| Theme | Agent Monitor source of truth |

## Goal

Make the default Agent Monitor consume Cortex Activity Timeline projection instead of using `execution-logs` as the user-facing source.

## Current-State Analysis

Cortex `/v1/trace/project` now returns safe user-facing records. App Monitor still renders the realtime Entangled `execution-logs` stream and adds phase labels locally. That is acceptable as a bridge, but it keeps execution logs doing product-surface work.

## Small Tickets

- [x] PR-169A — Business-owned Activity Timeline action.
  - Analyze: App has `agent_id` but should not derive Cortex root scope or call Cortex internals directly.
  - Implement: add `agents.activity_timeline` action in Business; it checks agent access, derives the main agent-root scope, calls Cortex `/v1/trace/project`, and returns only public records.
  - Test: Business unit tests cover scope derivation, Cortex request shape, safe response shape, and access validation.
  - Smoke: local action handler smoke with a mocked Cortex response.
  - Deploy: deploy services after merge.
  - GitHub: committed and pushed in `novaic-business` (`24a2072`); parent pointer updated in the PR-169A parent commit.
- [x] PR-169B — App hook and component for Activity Timeline.
  - Analyze: current ChatPanel subscribes to Entangled `execution-logs` for the normal monitor.
  - Implement: add a hook that calls `agents.activity_timeline`; add a user-facing Activity Timeline component rendering Observation / Reasoning / Action / Summary records.
  - Test: hook/client mapper tests and component tests prove raw debug fields are not rendered.
  - Smoke: app build/unit tests.
  - Deploy: deploy app/services as needed.
  - GitHub: committed and pushed in `novaic-app`; parent pointer updated in the PR-169B parent commit.
- [x] PR-169C — Default Agent Monitor uses Activity Timeline, not execution logs.
  - Analyze: `ChatPanel`, preview, expanded panel, and labels still say execution log.
  - Implement: switch default monitor and preview to Activity Timeline; keep execution log only behind explicit developer diagnostics if still needed.
  - Test: ChatPanel tests or static guards verify normal monitor path does not import/render `ExecutionLog`.
  - Smoke: app build/unit tests.
  - Deploy: deploy app.
  - GitHub: committed and pushed in `novaic-app`; parent pointer updated in the PR-169C parent commit.
- [x] PR-169D — Guardrails against debug fallback in user monitor.
  - Analyze: previous monitor leaked `result_id`, raw MCP content, HTTP errors, and execution-log wording.
  - Implement: static tests/guards banning raw diagnostic field rendering in normal Activity Timeline components.
  - Test: guard tests for `result_id`, `_mcp_content`, raw HTTP body/stack trace, and `execution-logs` fallback.
  - Smoke: full relevant frontend tests.
  - Deploy: deploy app/services.
  - GitHub: committed and pushed in `novaic-app`; parent pointer updated in the PR-169D parent commit.

## Done Criteria

- Normal monitor source is Cortex projection.
- Execution logs are diagnostic-only.
- Message status remains delivery UI only.
- No result id, raw MCP content, raw HTTP payload, or stack trace appears in normal monitor.
