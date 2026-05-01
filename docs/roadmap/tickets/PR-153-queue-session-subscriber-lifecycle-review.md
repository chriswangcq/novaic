# PR-153 — Queue / Session / Subscriber Lifecycle Review

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Repos | novaic-business, novaic-agent-runtime, docs |
| Depends on | PR-152 |

## Goal

Confirm and enforce one lifecycle model for user-message triggering, DispatchSubscriber consumption, session serialization, pending triggers, ReactThink/ReactActions, wake finalize, and worker recovery.

## Why This Matters

The agent loop must not be controlled by multiple overlapping concepts such as read/unread status, subscriber branches, scheduler side effects, or ad hoc session retry paths. Ownership should be explicit and minimal.

## Required Process

For this big ticket:

1. Analyze the current live code and deployed behavior.
2. Create small implementation tickets for any concrete cleanup found.
3. Implement each small ticket one by one.
4. Confirm whether the lifecycle is closed.
5. If not closed, return to step 3; otherwise close this ticket and move to PR-154.

## Boundary Invariant

- DispatchSubscriber converts Business message outbox events into queue triggers.
- Queue Session Coordinator serializes `(agent_id, subagent_id)` sessions and owns pending triggers.
- Runtime/Saga workers execute ReAct tasks.
- Wake finalize performs structural lifecycle closeout, not durable summary generation.
- Read/delivered UI state does not control agent execution.

## Small Tickets

- [ ] [PR-153A — Remove Subscriber Switch Residue](PR-153A-remove-subscriber-switch-residue.md)
- [ ] [PR-153B — Centralize Buffered Input Ownership](PR-153B-centralize-buffered-input-ownership.md)
- [ ] [PR-153C — Lifecycle Loop Guardrail](PR-153C-lifecycle-loop-guardrail.md)

## Current-State Analysis

2026-05-02 scan found:

1. Business FastAPI no longer owns the dispatch loop; `main_subscriber.py` is started as a required subprocess by `scripts/start.sh`.
2. Queue Session Coordinator owns active sessions and pending triggers via `tq_active_sessions` and `tq_pending_triggers`.
3. Runtime `wake_finalize` structurally closes the wake scope and calls Queue `/session-ended`.
4. Residue: active subscriber comments still mention the old `subscriber_enabled` switch.
5. Real ownership bug: Subscriber still writes Cortex `/v1/scope/append_input` on buffered dispatches and transitions buffered messages to `claimed` for the active scope. That makes the old scope appear to own messages that should belong to the next wake produced by the pending trigger.

## Unit / Guardrail Tests

- [ ] Add tests or guardrails for any removed duplicate lifecycle paths.
- [ ] Confirm subscriber is required path, not optional/canary.
- [ ] Confirm pending trigger/session serialization invariants.

## Smoke / Deploy

- [ ] Smoke user message -> subscriber -> queue -> agent reply.
- [ ] Smoke quick consecutive messages do not create competing active sessions.
- [ ] Deploy affected services.

## Git / Merge

- [ ] Each small ticket can be committed independently where practical.
- [ ] Parent repo submodule bump / docs commit.
- [ ] Push `main`.
- [ ] Mark `[deployed]` only after deploy evidence is collected.
