# PR-93 — Render execution logs as user-facing events by default

| Field | Value |
| --- | --- |
| **Ticket** | PR-93 |
| **Status** | `[✓]` — App deployed + tests/smoke verified 2026-04-29 |
| **Scope** | `novaic-app` |
| **Depends on** | PR-92 preferred; compatible with old rows |
| **Invariant** | Default execution-log UI should explain what happened, not expose internal tool ids or join keys. |

## Problem

The App currently renders raw tool names (`chat_reply`, `skill_end`) and `result_id` in default cards. When a lightweight join key is treated as display payload, expanding a card can show a technical load failure, which is an implementation artifact rather than useful product feedback.

## Goal

Split execution-log rendering into two layers:

1. **Default user-facing layer**: semantic title and summary, such as `已回复`, `已保存上下文`, `正在思考`.
2. **Technical details layer**: raw tool name, `tool_call_id`, `result_id`, `factory_log_id`, scope/round ids, available only inside a diagnostic details section.

## Implementation Checklist

- [x] Add an App display helper that derives semantic title/summary from `display_kind`, `display_summary`, payload, or safe old-row fallbacks.
- [x] Stop treating lightweight `data.result_id` as a renderable result payload by default.
- [x] Keep lazy payload fetch support for real `log-payloads` details.
- [x] Move `result_id` and `factory_log_id` into collapsed technical details, not the default card summary.
- [x] Update the main-agent preview to use the same semantic helper and stop treating lightweight `result_id` as display payload.
- [x] Preserve reasoning content display; do not delete `reasoning_content` previews.

## Unit / Component Tests

- [x] Utility test: `data.result_id` alone does not become display result content.
- [x] Utility test: `chat_reply` displays as a reply event with reply text.
- [x] Utility test: `skill_end` displays as a context-saved event with report text.
- [x] Component test: default card does not show raw `result_id`.
- [x] Component test: `skill_end` with only `data.result_id` does not show a technical load failure.
- [x] Component test: technical details can still expose join keys when expanded.

## Smoke Test

- [x] Open App execution log after a fresh message.
- [x] Confirm collapsed rows show user-facing labels.
- [x] Expand `chat_reply` and `skill_end`; confirm no default technical load failure.
- [x] Confirm technical ids are still available inside diagnostic details.

## Deployment Checklist

- [x] Build App successfully.
- [x] Deploy / restart the App frontend bundle.
- [x] Verify production UI against at least one fresh run.

## GitHub / Commit Checklist

- [x] Commit App changes.
- [x] Push subrepo branch.
- [x] Bump parent repo submodule pointer and commit.

## Verification Evidence

- Local: `npm run test:unit -- src/components/Visual/executionLogUtils.test.ts src/components/Visual/ExecutionLog.test.tsx src/components/hooks/useLogs.test.ts` → 16 passed.
- Local: `npm run build` → success.
- Deployed: `./deploy frontend 0.3.0`.
- Frontend OTA: `https://relay.gradievo.com/resource/frontend/v0.3.0/` returned HTTP 200.
- Production smoke rows `1100..1103` contain the semantic fields consumed by the App default rendering.

## Rollback

Revert App rendering changes. Runtime semantic metadata is backward compatible and can remain.
