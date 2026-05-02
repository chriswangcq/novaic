# PR-165 — Notification Wake and Prompt Cutover

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-business`, `novaic-agent-runtime`, `novaic-cortex`, docs |
| Depends on | PR-164 |
| Theme | Agent loop / prompt boundary |

## Goal

Move agent wake and prompt assembly to the subject/environment model: prompt receives environment notifications and active work trajectory, not raw unobserved message bodies as hidden context.

The agent should explicitly read the environment when it needs message contents. Subscriber/session code should own triggering and serialization, while Cortex owns work trajectory and Environment owns notification lifecycle.

## Required Process

1. Analyze subscriber, queue, session, prompt builder, pending trigger, and wake finalize ownership.
2. Create small tickets for notification delivery, prompt cutover, and lifecycle finalization.
3. Implement one small ticket at a time.
4. For each small ticket: unit tests, smoke test, deploy plan/result, Git commit/merge evidence.
5. Confirm the old raw-message prompt path is deleted or guarded before closing.

## Planned Small Tickets

- PR-165A — Subscriber emits Environment notifications as the wake source.
- PR-165B — Prompt builder uses notification-only message hints.
- PR-165C — Wake scope close and notification processed/failure semantics.

## Current-State Analysis

Pending after PR-164.

## Boundary Invariants

- Message delivery trigger is not cognitive memory.
- Read/unread UI status does not control the agent loop.
- Prompt builder does not smuggle raw IM bodies into context.
- Session serialization has one owner.

## Done Criteria

- Same-sender message bursts still behave correctly.
- Agent can answer only after observing via tools.
- Wake close writes the intended scope summary.
- Guards prevent reintroducing raw IM replay or wake-summary fallback paths.

