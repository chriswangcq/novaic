# PR-73 — Improve folded-scope rendering and empty-summary policy

| Field | Value |
|---|---|
| **Ticket** | PR-73 |
| **Status** | `[ ]` |
| **Opened** | 2026-04-27 |
| **Owner** | __ |
| **Severity** | P1 LLM input quality — repeated `(no report)` folded scopes waste budget and confuse the model. |
| **Blocks** | Stable agent-root continuity rollout. |
| **Blocked by** | PR-70 so normal wake folds have meaningful summaries. |
| **Invariant** | Folded closed scopes should help the LLM recover continuity; empty folds should not dominate the request. |

## Intent

Once PR-70 makes normal wake summaries useful, clean up the rendering layer so old empty scopes and future edge cases do not flood the LLM request with `[Skill ... completed] (no report)`.

## Required Behavior

- Folded scopes with real summaries render in a compact, recognizable structure.
- Empty summaries are suppressed, capped, or rendered as concise metadata only when needed.
- Rendering differentiates wake scopes from ordinary child skill scopes when helpful.
- The DFS order remains stable: active path expanded, closed siblings folded in order.
- Token-budget behavior remains predictable.

## Acceptance Criteria

- A root with many old empty wake scopes does not produce a wall of `(no report)` messages.
- A root with useful summaries still exposes them in chronological DFS order.
- Rendered messages preserve enough metadata to debug scope identity when needed.
- Existing DFS recursion tests pass with updated expected rendering.

## Engineering Checklist

### Unit Tests

- `[ ]` Cortex StepTree test: empty folded scopes are suppressed or compacted per policy.
- `[ ]` Cortex StepTree test: non-empty folded summaries render unchanged or improved.
- `[ ]` DFS order test: active scope still expands and closed siblings stay ordered.
- `[ ]` Budget-oriented test: multiple empty folds do not exceed a small expected message count.

### Smoke Tests

- `[ ]` Run agent-root prepare against a root with old empty wakes.
- `[ ]` Confirm LLM input no longer begins with repeated `(no report)`.
- `[ ]` Confirm useful PR-70 summaries still appear.

### Deployment

- `[ ]` Deploy Cortex.
- `[ ]` Run health checks and inspect Cortex logs for prepare/render.
- `[ ]` Capture before/after LLM input excerpt.

### GitHub / Commit

- `[ ]` Commit implementation, tests, and this ticket update as one PR-sized commit.
- `[ ]` Commit message should reference PR-73.
- `[ ]` PR description must include render examples, tests, smoke, and deploy evidence.

## Out of Scope

- Summary generation itself.
- Old data migration beyond display policy.
