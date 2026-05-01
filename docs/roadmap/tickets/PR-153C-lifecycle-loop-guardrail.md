# PR-153C — Lifecycle Loop Guardrail

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-153 |
| Repos | novaic-business, novaic-agent-runtime, docs |

## Goal

Add guardrails for the single agent-loop ownership model: Business message outbox is drained only by Subscriber, Queue Session Coordinator owns active/pending session serialization, and Runtime wake finalize closes sessions structurally.

## Why This Matters

The main risk after PR-153B is regression: a future shortcut could reintroduce read/unread-driven waking, subscriber-side Cortex writes, or competing pending-trigger loops.

## Implementation Plan

1. [ ] Add static guardrails banning Subscriber -> Cortex `append_input` writes.
2. [ ] Add static guardrails banning read/delivered UI state as an agent-loop trigger.
3. [ ] Add focused session serialization tests for concurrent dispatch and pending drain.

## Unit / Guardrail Tests

- [ ] New PR-153 lifecycle guardrail tests pass.
- [ ] Existing queue/session/subscriber tests pass.

## Smoke / Deploy / Git

- [ ] Smoke user message -> subscriber -> queue -> agent reply.
- [ ] Smoke rapid consecutive messages remain serialized.
- [ ] Deploy affected services if code changes are made.
- [ ] Commit affected repos.
- [ ] Parent repo submodule/docs commit and push.
