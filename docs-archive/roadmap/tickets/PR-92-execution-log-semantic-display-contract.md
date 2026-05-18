# PR-92 — Add semantic display metadata to execution logs

| Field | Value |
| --- | --- |
| **Ticket** | PR-92 |
| **Status** | `[✓]` — Runtime deployed + production smoke verified 2026-04-29 |
| **Scope** | `novaic-agent-runtime` |
| **Depends on** | PR-86..PR-90 |
| **Invariant** | Execution log rows may carry technical join keys, but they must also expose a stable semantic display contract for normal UI rendering. |

## Problem

Execution logs currently expose low-level tool names and join keys (`chat_reply`, `skill_end`, `result_id`, `factory_log_id`) but do not tell the App what the user-facing meaning of an event is. The App therefore guesses from raw tool data and can show implementation details as primary UI.

## Goal

Add lightweight semantic metadata to Runtime execution-log `data` so the App can render normal timeline cards without parsing tool internals.

## Implementation Checklist

- [x] Add semantic fields for tool logs, at minimum `display_kind` and `display_summary`.
- [x] Map `chat_reply` to a reply-sent display kind and summarize with the user-visible reply text.
- [x] Map `skill_end` to a context-saved display kind and summarize with `report`.
- [x] Preserve existing technical fields (`tool`, `tool_call_id`, `result_id`) as diagnostics/join keys.
- [x] Add semantic fields for think logs without removing reasoning content or Factory join keys.
- [x] Keep Entangled execution rows lightweight; do not embed large payloads.

## Unit Tests

- [x] Runtime test: `chat_reply` running/complete broadcasts include semantic display metadata.
- [x] Runtime test: `skill_end` complete broadcast includes the `report` semantic summary.
- [x] Runtime test: think complete broadcast includes semantic display metadata and preserves `factory_log_id`.

## Smoke Test

- [x] Send a real chat request and verify execution-log rows include semantic fields.
- [x] Verify `result_id` still exists for tool completion rows.
- [x] Verify Factory log id still exists for think completion rows.

## Deployment Checklist

- [x] Deploy Runtime.
- [x] Confirm runtime logs show no tool execution regressions.
- [x] Confirm App still receives execution logs through Entangled.

## GitHub / Commit Checklist

- [x] Commit Runtime changes.
- [x] Push subrepo branch.
- [x] Bump parent repo submodule pointer and commit.

## Verification Evidence

- Local: `pytest tests/test_pr86_execution_log_metadata.py -q` → 6 passed.
- Deployed: `./deploy runtime`.
- Production smoke message: `PR92/93 smoke：请简短回复收到`.
- Production execution log rows:
  - `1100` think: `display_kind=thinking`, `factory_log_id=9d14f062-d8f9-485b-8171-e96337dce5ca`.
  - `1101` chat_reply: `display_kind=reply_sent`, `display_summary=收到！✅`, `result_id=step-result:...:chat_reply:0`.
  - `1103` skill_end: `display_kind=context_saved`, `display_summary=用户PR92/93 smoke测试消息...`, `result_id=step-result:...:skill_end:1`.

## Rollback

Revert Runtime metadata projection only. Existing App fallback must continue to render rows without semantic fields.
