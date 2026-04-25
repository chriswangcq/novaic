# PR-66 — Make system-created child scopes render through the DFS step tree

| Field | Value |
|---|---|
| **Ticket** | PR-66 |
| **Status** | `[ ]` |
| **Opened** | 2026-04-25 |
| **Owner** | __ |
| **Severity** | P0 context correctness — agent-root wake scopes need fold/expand without fake historical prompt blocks. |
| **Blocks** | PR-67 |
| **Blocked by** | PR-65 |
| **Invariant** | A child scope recorded in `steps/_index.jsonl` must be renderable as closed fold or open expansion even when it was system-created. |

## Intent

Current ContextEngine folds closed scopes by finding `skill_begin(scope_id=...)` messages in `context.jsonl` and matching them to StepTree nodes.

Agent-root wake scopes may be system-created, so the renderer needs a first-class way to represent scope nodes from the step tree itself.

## Required Behavior

- Closed child scope under agent root renders as one fold message using its `summary.md`.
- Open child scope under agent root expands in DFS order.
- Existing LLM-created skill scopes continue to work.
- No child scope internals leak after that child is closed.
- Rendering must not require `<PREV_SCOPE_HISTORY>` / `<PREV_SCOPE_TAIL>`.

## Acceptance Criteria

- Unit test: closed system-created wake scope folds to summary.
- Unit test: current open wake scope expands.
- Unit test: nested closed skill under open wake still folds.
- Unit test: nested open skill under open wake still expands.
- Drift behavior is explicit and logged.

## Engineering Checklist

### Unit Tests

- Add Cortex `ContextEngine` tests for system-created child scopes without LLM `skill_begin` anchors.
- Preserve existing PR-39 tests for LLM-created nested scope fold behavior.
- Add a regression test proving closed child internals do not leak after fold.

### Smoke Tests

- Create an agent root with one closed wake child and one open wake child in a staging/prod-like workspace.
- Call `context/prepare_for_llm` and verify folded/expanded output shape.
- Confirm no `<PREV_SCOPE_HISTORY>` / `<PREV_SCOPE_TAIL>` is needed for that continuity signal.

### Deployment

- Deploy Cortex.
- Verify `/v1/context/prepare_for_llm` still works for existing normal scopes and new system child scopes.
- Capture log evidence for fold/expand decisions.

### GitHub / Commit

- Commit implementation and tests together.
- PR description must include before/after context-shape examples.

## Out of Scope

- Runtime wake lifecycle rewiring.
- Long-horizon compaction of old folded wake scopes.
