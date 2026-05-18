# PR-153C — Lifecycle Loop Guardrail

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-153 |
| Repos | novaic-business, novaic-agent-runtime, docs |

## Goal

Add guardrails for the single agent-loop ownership model: Business message outbox is drained only by Subscriber, Queue Session Coordinator owns active/pending session serialization, and Runtime wake finalize closes sessions structurally.

## Why This Matters

The main risk after PR-153B is regression: a future shortcut could reintroduce read/unread-driven waking, subscriber-side Cortex writes, or competing pending-trigger loops.

## Implementation Plan

1. [x] Add static guardrails banning Subscriber -> Cortex `append_input` writes.
2. [x] Add static guardrails banning read/delivered UI state as an agent-loop trigger.
3. [x] Add focused session serialization tests for concurrent dispatch and pending drain.

## Unit / Guardrail Tests

- [x] New PR-153 lifecycle guardrail tests pass.
- [x] Existing queue/session/subscriber tests pass.

## Smoke / Deploy / Git

- [x] Smoke user message -> subscriber -> queue -> agent reply.
- [x] Smoke rapid consecutive messages remain serialized.
- [x] Deploy affected services if code changes are made.
- [x] Commit affected repos.
- [ ] Parent repo submodule/docs commit and push.

## Evidence

- Added `scripts/ci/lint_lifecycle_loop_ownership.sh`: bans Subscriber Cortex input writes and Subscriber message transition writes, checks Queue pending metadata merge exists, checks Runtime `session.init` bulk-claims inputs, and runs the existing `chat_messages.read` UI-only guard.
- Added `novaic-business/tests/test_pr153_lifecycle_guardrails.py`: source-level guard that Subscriber cannot regain append/transition write paths.
- Expanded `novaic-agent-runtime/tests/test_pr153_pending_inbox_metadata.py`: concurrent dispatches for the same `(agent_id, subagent_id)` now assert one active session and one pending inbox projection, with buffered message IDs owned by the restarted wake.
- Bug found and fixed while adding the guardrail: a concurrent active-session insert loser used to return `deduped` and drop the trigger; it now cancels its transient saga, buffers the trigger metadata, and returns `buffered`.
- Tests:
  - `scripts/ci/lint_lifecycle_loop_ownership.sh` → PASS.
  - `novaic-business`: `python3 -m pytest tests/test_dispatch_subscriber.py tests/test_im_aggregation.py tests/test_pr52_stale_claim_check.py tests/test_pr153_lifecycle_guardrails.py -q` → 63 passed.
  - `novaic-agent-runtime`: `python3 -m pytest tests/test_pr153_pending_inbox_metadata.py tests/test_session_init_message_ids.py tests/test_scope_end_consumed.py tests/test_context_read_by_ids.py -q` → 23 passed.
- Deploy smoke: `./deploy gateway` restarted all backend services and required Subscriber; `./deploy status` shows backend ports healthy and relay active.
