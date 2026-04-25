# PR-65 — Introduce long-lived agent root scope lifecycle

| Field | Value |
|---|---|
| **Ticket** | PR-65 |
| **Status** | `[ ]` |
| **Opened** | 2026-04-25 |
| **Owner** | __ |
| **Severity** | P0 architecture — establishes the new cross-wake continuity anchor. |
| **Blocks** | PR-66, PR-67, PR-69 |
| **Blocked by** | PR-64 for clean prod validation. |
| **Invariant** | Each `(user_id, agent_id, subagent_id)` has one system-managed agent root scope that stays active across wakes. |

## Intent

Create a permanent agent root scope as the cross-wake continuity container.

This root is not a normal per-wake root and is not archived at the end of each turn.

## Required Behavior

- On wake, Runtime can resolve or create `agent_root_scope_id`.
- Agent root scope is idempotent: repeated wake initialization reuses the same active root.
- Agent root scope is system-managed and not presented to the LLM as a scope it should close.
- Existing active-scope DFS behavior inside normal child scopes remains unchanged.

## Acceptance Criteria

- Repeated wakes for the same `(user, agent, subagent)` reuse the same agent root scope.
- Resting after a chat reply does not archive the agent root scope.
- Diagnostics can show the mapping from subagent to agent root scope.
- Existing single-scope tests still pass under legacy mode or updated expectations.

## Engineering Checklist

### Unit Tests

- Add or update Runtime/Cortex tests for idempotent agent-root creation.
- Add tests that rest/archive closes only the wake child scope and leaves agent root active.
- Add tests for diagnostics/mapping lookup from `(user_id, agent_id, subagent_id)` to `agent_root_scope_id`.

### Smoke Tests

- Start two consecutive wakes for the same 小牛 subagent.
- Verify the agent root scope id is identical across wakes.
- Verify root phase remains `executing` after the first wake rests.

### Deployment

- Deploy all touched services, likely `cortex` and `services`/runtime.
- Verify health endpoints and worker status after deploy.
- Capture at least two online evidence points: scope meta/status and service logs or metrics.

### GitHub / Commit

- Commit implementation and tests as one PR-sized change.
- PR description must link this ticket and include unit-test output, smoke evidence, and deploy evidence.

## Out of Scope

- Context rendering of wake child scopes.
- Removal of `<PREV_SCOPE_HISTORY>` / `<PREV_SCOPE_TAIL>`.
- Compact/fusion for very long agent root timelines.
