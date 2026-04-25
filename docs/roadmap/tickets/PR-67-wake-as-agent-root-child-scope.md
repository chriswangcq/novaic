# PR-67 — Rewire wake lifecycle so each wake is a child scope under agent root

| Field | Value |
|---|---|
| **Ticket** | PR-67 |
| **Status** | `[ ]` |
| **Opened** | 2026-04-25 |
| **Owner** | __ |
| **Severity** | P0 behavior — this replaces cross-wake prompt injection with scope-tree continuity. |
| **Blocks** | PR-68, PR-69 |
| **Blocked by** | PR-65, PR-66 |
| **Invariant** | A wake closes its own wake child scope; it must not close or archive the agent root scope. |

## Intent

Change Runtime session initialization and rest behavior:

- `session.init` ensures agent root scope.
- It creates a current wake child scope under that root.
- `context.prepare_for_llm` prepares messages from the agent root scope.
- Current user input belongs to the current wake child scope.
- Rest closes the wake child scope, leaving agent root active.

## Required Behavior

- Current wake is visible as the active expanded subtree.
- Prior wakes are closed folded child scopes.
- Tool execution routes to the deepest active scope under the current wake.
- Active stack shown to LLM points at the current wake/skill stack, not at agent root as a closable target.

## Acceptance Criteria

- Two consecutive wakes produce one agent root with two wake child scopes.
- The second wake's LLM call sees the first wake only as a folded summary, not a raw `<PREV_SCOPE_TAIL>` replay.
- `subagent_rest` or equivalent turn-finalizer closes the wake child scope.
- Agent root remains `phase=executing`.

## Engineering Checklist

### Unit Tests

- Add Runtime session-init tests for creating wake child scope under existing agent root.
- Add rest/finalizer tests proving wake child closes and agent root stays active.
- Add context-prepare tests proving LLM call is assembled from agent root while current input lands in the current wake child.

### Smoke Tests

- Run a two-turn 小牛 conversation.
- Inspect the second LLM call: previous wake is folded; current wake is expanded.
- Verify no runtime active session points at the agent root as a closable per-turn scope.

### Deployment

- Deploy Runtime services and Cortex if touched.
- Confirm queue workers are healthy after deploy.
- Capture online evidence: scope tree shape, current LLM request shape, and rest/archive logs.

### GitHub / Commit

- Commit implementation, tests, and docs together.
- PR description must include unit-test output, smoke transcript, deployment target, and rollback plan.

## Out of Scope

- Summary quality beyond using `skill_end.report`.
- User profile facts.
- Old data migration.
