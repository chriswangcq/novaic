# PR-165C — Notification Lifecycle Close / Failure Semantics

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-agent-runtime`, `novaic-business`, docs |
| Depends on | PR-165B |
| Theme | Lifecycle ownership |

## Goal

Confirm and tighten notification lifecycle ownership after prompt cutover:
`session_init` claims wake notifications, successful wake close marks them
processed/consumed, and failure paths leave enough state for recovery without
pretending a message was observed or handled.

## Plan

1. Audit `session_init`, pending-trigger buffering, `scope_end`, health
   recovery, and Business Environment transition code.
2. Add tests for success, archive failure, and missing/invalid notification id
   semantics.
3. Remove or guard any remaining path that treats read/unread UI status as
   agent-loop state.
4. Smoke a normal wake close and a forced failure/recovery shape where feasible.
5. Deploy, verify, and commit.

## Required Tests

- Runtime lifecycle test: successful wake close transitions current
  notification ids to processed/consumed.
- Runtime/business test: failed close does not mark notifications processed.
- Guardrail test: agent loop does not consult UI read/unread status.

## Done Criteria

- Notification lifecycle has one owner chain: Subscriber/Queue -> Runtime
  session -> Environment/Business transitions.
- UI message status remains delivery/read presentation only.
- Tests, smoke, deploy, and git commit evidence are recorded here.

