# PR-94 — Make execution-log expanded view an Agent Monitor, not a debug panel

| Field | Value |
| --- | --- |
| **Ticket** | PR-94 |
| **Status** | `[✓]` |
| **Scope** | `novaic-app` |
| **Depends on** | PR-92, PR-93 |
| **Invariant** | The execution-log area is an Agent Monitor: users should see what the agent is doing, not tool-call internals. |

## Problem

PR-93 made collapsed execution-log rows semantic, but the expanded state still exposes debug concepts such as `Input Parameters`, `Execution Result`, `技术详情`, raw JSON, and join keys. That makes the monitor feel like a developer diagnostic panel.

## Goal

Keep the whole expanded state user-facing. A user should be able to open a row and understand:

- what the agent did;
- whether it succeeded;
- the useful human-readable result or summary.

## Design

The execution-log expanded state should render a deterministic monitor detail block derived from the semantic display contract:

- `think` / `display_kind=thinking` -> `思考摘要`;
- `chat_reply` / `display_kind=reply_sent` -> `回复内容`;
- `skill_end` / `display_kind=context_saved` -> `上下文摘要`;
- failed rows -> short failure reason.

The monitor uses `display_summary` first, then safe local fallbacks. It must not show join keys, raw JSON, LLM request payloads, tool parameter/result dumps, or TRS/Factory ids in the normal user-facing surface.

## Non-Goals

- Do not delete technical fields from Entangled rows.
- Do not remove Runtime `result_id` / `factory_log_id`.
- Do not add LLM-generated log summaries.
- Do not create a new developer diagnostics panel in this PR.

## Implementation Checklist

- [x] Remove debug blocks from `LogCard` expanded state:
  - `Input Parameters`
  - `Execution Result`
  - `技术详情`
  - raw JSON / `SmartValue`
  - LLM input modal / debug request entry
- [x] Keep expanded state deterministic and semantic.
- [x] Show `chat_reply` expanded detail as reply content.
- [x] Show `skill_end` expanded detail as saved context summary.
- [x] Show `think` expanded detail as thinking summary.
- [x] Show failed steps with a short human-readable failure summary.
- [x] Keep the collapsed main-agent preview semantic.

## Unit / Component Tests

- [x] Component test: expanded think row with `factory_log_id` does not show Factory ids or technical details.
- [x] Component test: expanded `chat_reply` shows reply content and does not show `result_id`.
- [x] Component test: expanded `skill_end` shows context summary and no debug / TRS 404 text.
- [x] Component test: failed tool row shows human failure summary and not `Execution Result` / raw JSON labels.

## Smoke Test

- [x] Build App successfully.
- [x] Deploy frontend OTA.
- [x] Verify production semantic log rows are available for rendering.
- [x] Verify expanded monitor rows have no visible debug ids/labels in component tests.

## Deployment Checklist

- [x] `npm run test:unit -- src/components/Visual/executionLogUtils.test.ts src/components/Visual/ExecutionLog.test.tsx src/components/hooks/useLogs.test.ts`
- [x] `npm run build`
- [x] `./deploy frontend 0.3.0`
- [x] Frontend OTA URL returns HTTP 200.

## GitHub / Commit Checklist

- [x] Commit App changes.
- [x] Push subrepo branch.
- [x] Bump parent repo submodule pointer and commit.

## Rollback

Revert the App display changes. Runtime semantic metadata remains backward compatible.
