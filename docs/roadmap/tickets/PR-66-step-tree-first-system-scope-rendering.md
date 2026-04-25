# PR-66 — Make system-created child scopes render through the DFS step tree

| Field | Value |
|---|---|
| **Ticket** | PR-66 |
| **Status** | `[✓]` |
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

- `[x]` Add Cortex `ContextEngine` tests for system-created child scopes without LLM `skill_begin` anchors.
- `[x]` Preserve existing PR-39 tests for LLM-created nested scope fold behavior.
- `[x]` Add a regression test proving closed child internals do not leak after fold.

### Smoke Tests

- `[x]` Create an agent root with one closed wake child and one open wake child in a staging/prod-like workspace.
- `[x]` Call `context/prepare_for_llm` and verify folded/expanded output shape.
- `[x]` Confirm no `<PREV_SCOPE_HISTORY>` / `<PREV_SCOPE_TAIL>` is needed for that continuity signal.

### Deployment

- `[x]` Deploy Cortex.
- `[x]` Verify `/v1/context/prepare_for_llm` still works for existing normal scopes and new system child scopes.
- `[x]` Capture log evidence for fold/expand decisions.

### GitHub / Commit

- `[x]` Commit implementation and tests together.
- `[x]` PR description must include before/after context-shape examples.

## Completion Notes

Implemented Cortex step-tree-first rendering for system-created child scopes:

- `StepNode` now carries `scope_path` and open-scope `context_messages`.
- `ContextEngine` still honors existing LLM-created `skill_begin(scope_id=...)` anchors.
- Any direct child scope in `steps/_index.jsonl` without an anchor now renders from the step tree:
  - closed child → one `render_scope_fold(...)` summary message;
  - open child → recursively merges that child scope's own `context.jsonl` and child step tree.
- Existing drift behavior remains explicit: anchored `skill_begin` without a matching scope node falls through and logs a warning.

Validation:

- Unit tests:
  - `pytest -q tests/test_pr66_system_scope_rendering.py tests/test_context_engine_dfs.py` → `14 passed`.
  - `pytest -q` in `novaic-cortex` → `383 passed, 16 skipped`.
- Deployment:
  - `./deploy cortex` completed successfully on 2026-04-25; backend restart reported Cortex `:19996` OK.
- Production smoke evidence:
  - Evidence log: `/opt/novaic/data/backups/pr66_system_scope_render_smoke_20260425_181721.log`.
  - Seeded agent root `pr66-root-20260425101721` with:
    - closed child `wake-closed`, summary `closed wake summary`;
    - open child `wake-open`, context `system prompt in open wake` + `open child visible request`.
  - `/v1/context/prepare_for_llm` returned:
    - `[Skill 'wake closed' completed]\nclosed wake summary`;
    - `system prompt in open wake`;
    - `open child visible request`.
  - Assertion passed that closed child internal text did not leak and no `<PREV_SCOPE_HISTORY>` / `<PREV_SCOPE_TAIL>` block was required.
  - Cortex log evidence captured:
    - `folded unanchored closed scope_id=wake-closed name=wake closed`;
    - `expanding unanchored open scope_id=wake-open name=wake open context=2 children=0`.

Git:

- Cortex submodule commit: `7c073a7 cortex: render system scope nodes from step tree`.

## Out of Scope

- Runtime wake lifecycle rewiring.
- Long-horizon compaction of old folded wake scopes.
