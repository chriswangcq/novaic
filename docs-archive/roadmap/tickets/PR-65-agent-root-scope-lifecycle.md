# PR-65 — Introduce long-lived agent root scope lifecycle

| Field | Value |
|---|---|
| **Ticket** | PR-65 |
| **Status** | `[✓]` |
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

- `[x]` Add or update Runtime/Cortex tests for idempotent agent-root creation.
- `[x]` Add tests that rest/archive closes only the wake child scope and leaves agent root active.
- `[x]` Add tests for diagnostics/mapping lookup from `(user_id, agent_id, subagent_id)` to `agent_root_scope_id`.

### Smoke Tests

- `[x]` Start two consecutive wakes for the same 小牛 subagent.
- `[x]` Verify the agent root scope id is identical across wakes.
- `[x]` Verify root phase remains `executing` after the first wake rests.

### Deployment

- `[x]` Deploy all touched services, likely `cortex` and `services`/runtime.
- `[x]` Verify health endpoints and worker status after deploy.
- `[x]` Capture at least two online evidence points: scope meta/status and service logs or metrics.

### GitHub / Commit

- `[x]` Commit implementation and tests as one PR-sized change.
- `[x]` PR description must link this ticket and include unit-test output, smoke evidence, and deploy evidence.

## Completion Notes

Implemented an additive PR-65 foundation in Runtime:

- `session.init` now derives a stable system-managed agent-root scope id from `subagent_id`.
- Each wake idempotently creates that root scope before creating the normal per-wake scope.
- `agent_root_scope_id` is written to session meta and returned from `session.init` for diagnostics and later PR-67 wiring.
- The LLM-visible active scope remains the existing per-wake root until PR-67; this keeps current DFS behavior unchanged.

Validation:

- Unit tests:
  - `pytest -q tests/test_pr65_agent_root_scope.py tests/test_scope_end_consumed.py tests/test_session_init_message_ids.py tests/test_wake_im_replay.py -q` → `54 passed`.
  - `pytest -q` in `novaic-agent-runtime` → `261 passed in 0.99s`.
- Deployment:
  - `./deploy services` completed successfully on 2026-04-25.
  - Health checks after smoke: Business `19998`, Queue `19997`, Cortex `19996` all healthy.
- Production smoke evidence:
  - Evidence log: `/opt/novaic/data/backups/pr65_agent_root_smoke_20260425_180734.log`.
  - Two system wakes for 小牛:
    - Wake 1 scope `32449929-d0cb-42cb-9dbb-2ad83333fa47` archived with tail found.
    - Wake 2 scope `ee53c4de-7173-4550-91a7-5772d3cec961` archived with tail found.
  - Agent root `agent-root-main-415f6cfd` remained active after both wakes:
    - after wake 1: `phase=executing`, `start_time=1777111655.194436`.
    - after wake 2: `phase=executing`, same `start_time=1777111655.194436`.
  - Final subagent state: `sleeping`, `last_scope_id=ee53c4de-7173-4550-91a7-5772d3cec961`, active queue sessions `0`.
  - Cortex log evidence: `scope.created scope_id='agent-root-main-415f6cfd' skill='agent_root' name='agent root: main-415f6cfd' parent='(root)'`.

Git:

- Runtime submodule commit: `ad8c9c1 runtime: add agent root scope foundation`.

## Out of Scope

- Context rendering of wake child scopes.
- Removal of `<PREV_SCOPE_HISTORY>` / `<PREV_SCOPE_TAIL>`.
- Compact/fusion for very long agent root timelines.
