# PR-67 — Rewire wake lifecycle so each wake is a child scope under agent root

| Field | Value |
|---|---|
| **Ticket** | PR-67 |
| **Status** | `[✓]` |
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

- `[x]` Add Runtime session-init tests for creating wake child scope under existing agent root.
- `[x]` Add rest/finalizer tests proving wake child closes and agent root stays active.
- `[x]` Add context-prepare tests proving LLM call is assembled from agent root while current input lands in the current wake child.

### Smoke Tests

- `[x]` Run a two-turn 小牛 conversation.
- `[x]` Inspect the second LLM call: previous wake is folded; current wake is expanded.
- `[x]` Verify no runtime active session points at the agent root as a closable per-turn scope.

### Deployment

- `[x]` Deploy Runtime services and Cortex if touched.
- `[x]` Confirm queue workers are healthy after deploy.
- `[x]` Capture online evidence: scope tree shape, current LLM request shape, and rest/archive logs.

### GitHub / Commit

- `[x]` Commit implementation, tests, and docs together.
- `[x]` PR description must include unit-test output, smoke transcript, deployment target, and rollback plan.

## Completion Notes

Implemented the agent-root wake-child lifecycle:

- Runtime `session.init` now ensures the stable `agent_root_scope_id`, creates each wake as a `skill="wake"` child under that root, and writes system/current context into the wake child's `context.jsonl`.
- React think/actions/rest now carry both addresses:
  - `scope_id` remains the per-wake id used by Queue/session lifecycle and finalizer idempotency.
  - `agent_root_scope_id` is the Cortex assembly root.
  - `wake_scope_path` is the explicit write/close target for current-wake context and metadata.
- Cortex internal APIs now accept explicit `scope_path` for context/meta/input writes and can resolve a child scope by bare wake `scope_id` for buffered dispatch compatibility.
- Rest closes the wake child (`is_root=false`) and auto-closes any still-open children under that wake; the agent root remains `phase=executing`.
- The LLM-visible active stack hides the system-managed wake frame, so the model is not instructed to close the wake child directly.

Validation:

- Unit tests:
  - `pytest -q` in `novaic-agent-runtime` → `265 passed`.
  - `pytest -q` in `novaic-cortex` → `386 passed, 16 skipped`.
- Deployment:
  - `./deploy runtime` completed successfully on 2026-04-25; backend restart reported all API services OK.
  - `./deploy cortex` completed successfully on 2026-04-25; backend restart reported all API services OK.
  - `./deploy status` showed Queue Service `:19997`, Cortex `:19996`, and 8 worker processes healthy.
- Production smoke evidence:
  - Evidence log: `/opt/novaic/data/backups/pr67_wake_child_scope_smoke_20260425_183653.log`.
  - Smoke agent: `agent_id=pr67-smoke-agent-20260425_183653`, `subagent_id=main-pr67-smoke`, root `agent-root-main-pr67-smoke`.
  - Wake children:
    - `pr67-wake-1-20260425_183653` at `/ro/active/agent-root-main-pr67-smoke/steps/0001_scope_pr67-wake-1-20260425_183653`, closed as a lifecycle container.
    - `pr67-wake-2-20260425_183653` at `/ro/active/agent-root-main-pr67-smoke/steps/0002_scope_pr67-wake-2-20260425_183653`, expanded during prepare, then closed.
  - Second prepare assertions passed:
    - explicit child skill summary present;
    - first wake raw context absent;
    - current wake input present;
    - no `<PREV_SCOPE_TAIL>` or `<PREV_SCOPE_HISTORY>` in assembled messages.
  - Metadata assertions passed:
    - root stayed `phase=executing`;
    - wake1 and wake2 ended `phase=archived`;
    - root `current_wake_scope_id` pointed at wake2 during the second wake.

Rollback plan:

- Revert Runtime commit `8fcd577` and Cortex commit `ab00143`, then deploy `runtime` and `cortex`.
- If an emergency rollback is needed before code revert, stop sending `agent_root_scope_id` / `wake_scope_path` from Runtime payloads; Cortex endpoints remain backwards-compatible with root-scope callers.

Git:

- Runtime submodule commit: `8fcd577 runtime: route wakes through agent root child scopes`.
- Cortex submodule commit: `ab00143 cortex: target wake child scopes by path`.

## Out of Scope

- Summary quality beyond using `skill_end.report`.
- User profile facts.
- Old data migration.
