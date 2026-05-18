# PR-233 — Active IM Delivery vs Wake Creation Hardening

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-05 |
| Repos | `novaic-agent-runtime`, `novaic-cortex`, docs |
| Depends on | PR-153, PR-168, PR-186 |
| Theme | Agent loop lifecycle / explicit dependency boundary |

## Goal

Separate **message delivery** from **wake creation** so a user IM sent while an
agent is already awake is delivered to the current wake inbox instead of
creating a competing wake or being hidden in a pending trigger that the active
loop cannot observe.

## Current-State Analysis

The current Queue session coordinator has one overloaded decision point:

1. If no active session exists, `SessionRepository.dispatch()` creates a new
   wake saga.
2. If an active session exists, the same method writes the new trigger into
   `tq_pending_triggers`.
3. `tq_pending_triggers` is only drained by `session_ended()`, so a message sent
   while the agent is still awake may not be visible to the running wake.
4. When a wake is stuck or `wake_finalize` fails, the Queue watchdog may remove
   the active-session row while Cortex still has an open child skill. A later IM
   can then create a new wake even though the previous Cortex stack is still not
   structurally closed.

This violates the product contract:

- Active / alive wake: deliver new IM to the current wake inbox and make the
  next context round inject a notification.
- Sleeping / no active session: create a new wake.
- Dead / stuck active session: declare recovery, archive the old structure, and
  migrate pending inbox to the recovery wake.
- Open Cortex child skill must not be treated as a healthy wake continuation.

## Explicit Dependency Boundary

All behavior-changing decisions must be testable from explicit inputs:

- active-session snapshot
- trigger type and notification/message ids
- heartbeat/dead-session snapshot
- clock/id provider values
- Cortex scope state snapshot

Queue decision logic must not rely on hidden database reads, current time, or
ambient process state inside the core decision function. Repositories and
runtime handlers may perform IO at the boundary, then pass typed snapshots into
core logic.

## Small Tickets

- [x] [PR-233A — Queue active inbox dispatch decision](PR-233A-session-dispatch-active-inbox.md)
- [x] [PR-233B — Runtime `session.attach_input` active wake delivery](PR-233B-runtime-session-attach-input.md)
- [x] [PR-233C — Dead active session recovery and structural archive](PR-233C-dead-active-session-recovery.md)
- [x] [PR-233D — Context/im_read observation guardrails and end-to-end tests](PR-233D-context-attached-input-observation-guards.md)

## Implementation Result

Implemented in `novaic-agent-runtime`:

- Active user/subagent IM dispatch now routes to `session.attach_input` and
  returns `attached_to_active`.
- Sleeping/no-active dispatch still creates `subagent_wake`.
- Non-attachable active triggers still use `tq_pending_triggers`.
- `wake_finalize` failure now records `tq_session_recoveries`, clears the
  active row, and enqueues idempotent `cortex.scope_end` structural archival.
- The next dispatch after recovery starts a `recovered` wake and carries any
  orphan pending message ids into the new wake context.

## Acceptance Criteria

- New IM while an agent has a healthy active wake does not create a new wake.
- The IM is appended to the current wake input set and becomes visible through
  `im_read` after context preparation.
- Sleeping agents still create a fresh wake on new IM.
- Stuck active sessions are treated as recovery, not normal continuation.
- Cortex dangling child skills are force-archived or marked closed before a
  recovery wake is considered healthy.
- Unit tests prove Queue decisions are deterministic from explicit snapshots.
- Runtime tests prove `session.attach_input` updates Cortex input and claims the
  corresponding Environment notifications without hidden inputs.

## Deploy Result

2026-05-06:

- `./deploy runtime` synced `novaic-common` and `novaic-agent-runtime`, then
  restarted all backend services through remote `start.sh`.
- `./deploy status` reported Entangled, Gateway, Business, Device, Queue
  Service, Blob Service, Cortex, 8 workers, and Relay healthy.
- Runtime/worker log spot check found no startup error/traceback/exception.

## Verification Plan

- Runtime unit tests for dispatch decisions.
- Runtime handler tests for `session.attach_input`.
- Context/im_read tests for attached notification visibility.
- Saga/session recovery tests for stuck active rows and pending inbox migration.
- Guardrail grep for old "active means pending trigger" assumptions.

## Deployment Checklist

- [x] Runtime tests pass locally.
- [x] Cortex tests impacted by scope lifecycle pass locally.
- [ ] Parent repo submodule pointer is updated if subrepos change.
- [x] Runtime service deployed.
- [ ] Smoke: send IM while agent is active; verify no new wake is created.
- [ ] Smoke: kill/stall active wake; send IM; verify recovery wake receives the pending input.
