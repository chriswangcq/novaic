# PR-153 — Queue / Session / Subscriber Lifecycle Review

| Field | Value |
| --- | --- |
| Status | `[closed]` |
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

- [x] [PR-153A — Remove Subscriber Switch Residue](PR-153A-remove-subscriber-switch-residue.md)
- [x] [PR-153B — Centralize Buffered Input Ownership](PR-153B-centralize-buffered-input-ownership.md)
- [x] [PR-153C — Lifecycle Loop Guardrail](PR-153C-lifecycle-loop-guardrail.md)

## Current-State Analysis

2026-05-02 scan found:

1. Business FastAPI no longer owns the dispatch loop; `main_subscriber.py` is started as a required subprocess by `scripts/start.sh`.
2. Queue Session Coordinator owns active sessions and pending triggers via `tq_active_sessions` and `tq_pending_triggers`.
3. Runtime `wake_finalize` structurally closes the wake scope and calls Queue `/session-ended`.
4. Residue: active subscriber comments still mention the old `subscriber_enabled` switch.
5. Real ownership bug: Subscriber still writes Cortex `/v1/scope/append_input` on buffered dispatches and transitions buffered messages to `claimed` for the active scope. That makes the old scope appear to own messages that should belong to the next wake produced by the pending trigger.

2026-05-02 closure:

1. Subscriber switch/disabled residue is removed from active code and guarded by `scripts/ci/lint_agent_loop_path.sh`.
2. Subscriber no longer writes Cortex scope input or message lifecycle claimed transitions. It drains outbox rows into Queue and marks outbox delivery/failure only.
3. Queue pending triggers now merge `message_ids` across overwrites and also buffer concurrent active-session insert losers instead of returning `deduped`.
4. Runtime `session.init` is the single owner for wake input registration and `claimed` transitions.
5. `scripts/ci/lint_lifecycle_loop_ownership.sh` guards this ownership split and also runs the existing `chat_messages.read` UI-only lint.

## Unit / Guardrail Tests

- [x] Add tests or guardrails for any removed duplicate lifecycle paths.
- [x] Confirm subscriber is required path, not optional/canary.
- [x] Confirm pending trigger/session serialization invariants.

## Smoke / Deploy

- [x] Smoke user message -> subscriber -> queue -> agent reply.
- [x] Smoke quick consecutive messages do not create competing active sessions.
- [x] Deploy affected services.

## Git / Merge

- [x] Each small ticket can be committed independently where practical.
- [x] Parent repo submodule bump / docs commit.
- [ ] Push `main`.
- [x] Mark `[deployed]` only after deploy evidence is collected.

## Evidence

- PR-153A: `scripts/ci/lint_agent_loop_path.sh` passed; subscriber tests passed; deployed with required Subscriber process.
- PR-153B: Business subscriber/aggregation/stale-claim tests passed; Runtime session/context/scope tests passed; Cortex suite passed; deployed.
- PR-153C: lifecycle ownership lint passed; Business lifecycle guard tests passed; Runtime concurrent dispatch serialization tests passed; deployed.
- Final deploy smoke: `./deploy gateway` and `./deploy status` show Entangled, Gateway, Business, Device, Queue, Storage, Cortex, Workers, Subscriber, and relay healthy.
