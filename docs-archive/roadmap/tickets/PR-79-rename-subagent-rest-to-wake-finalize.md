# PR-79 — Rename runtime `subagent_rest` to `wake_finalize`

| Field | Value |
| --- | --- |
| Status | `[x]` done |
| Severity | P1 conceptual cleanup |
| Owner | Codex |
| Branch | `codex/focus-new-llm-context` |

## Problem

`subagent_rest` is now only a runtime cleanup saga triggered after the active scope stack reaches zero. The name still suggests a user-visible rest tool or a second summary path, which keeps causing design confusion.

## Desired Contract

- LLM closes scopes with `skill_end(report=...)`.
- `stack_depth == 0` triggers `wake_finalize`.
- `wake_finalize` only performs runtime cleanup: structural Cortex close/no-op, subagent state update, parent notification, MCP teardown, and session-ended notification.
- `wake_finalize` never receives or writes summary text.

## Implementation Checklist

- [x] Rename saga file/definition from `subagent_rest` to `wake_finalize`.
- [x] Rename trigger payloads and idempotency keys to `wake-finalize-*`.
- [x] Rename `rest_reason` to `finalize_reason` inside runtime saga contexts.
- [x] Rename `stack_depth_at_rest` to `stack_depth_at_finalize`.
- [x] Update compensation/watchdog code to target `wake_finalize`.
- [x] Remove active-code references to `subagent_rest`.

## Unit Tests

- [x] Runtime tests assert trigger saga type is `wake_finalize`.
- [x] Runtime tests assert context carries `finalize_reason`.
- [x] Runtime tests assert compensation creates `wake_finalize`.
- [x] Runtime registry/worker tests assert `wake_finalize` is registered and `subagent_rest` is absent.

## Smoke Test

- [x] After deployment, trigger/inspect a finalize path and confirm no pending `subagent_rest` saga is created.
- [x] Confirm logs use `wake_finalize`.

## Deployment

- [x] Deploy agent-runtime.
- [x] Check runtime worker health.

## GitHub / Commit Work

- [x] Commit `novaic-agent-runtime` changes.
- [x] Commit parent repo submodule pointer and ticket.
- [x] Push branches.
