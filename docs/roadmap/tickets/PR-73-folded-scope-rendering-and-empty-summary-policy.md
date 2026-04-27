# PR-73 — Improve folded-scope rendering and empty-summary policy

| Field | Value |
|---|---|
| **Ticket** | PR-73 |
| **Status** | `[✓]` |
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

- `[x]` Cortex StepTree test: empty folded scopes are suppressed or compacted per policy.
- `[x]` Cortex StepTree test: non-empty folded summaries render unchanged or improved.
- `[x]` DFS order test: active scope still expands and closed siblings stay ordered.
- `[x]` Budget-oriented test: multiple empty folds do not exceed a small expected message count.

Evidence:

- `cd novaic-cortex && pytest -q tests/test_pr73_folded_scope_rendering.py tests/test_pr66_system_scope_rendering.py tests/test_context_engine_dfs.py` → `19 passed in 0.06s`
- `cd novaic-cortex && pytest -q` → `393 passed, 16 skipped in 0.78s`

### Smoke Tests

- `[x]` Run agent-root prepare against a root with old empty wakes.
- `[x]` Confirm LLM input no longer begins with repeated `(no report)`.
- `[x]` Confirm useful PR-70 summaries still appear.

Evidence:

- Production 小牛 message `3633ff4394f2`: `PR73 smoke：请简短回复收到2`.
- Agent reply `4875ffa40d5e`: `收到！✅`.
- Root prepare after PR-73:
  - `message_count 5`
  - `has_no_report False`
  - `wake_labels 5`
  - `has_dage True`
  - `has_pr72 True`
  - `has_pr73 True`
- Root prepare excerpt now starts with useful folds such as:
  - `[Wake 'user conversation' completed]`
  - `Wake summary:`
  - `Durable fact: User asked to be called 大哥.`
- Cortex logs for smoke scope `54dd7d87-83b0-463b-a9d6-58437edc1746` showed seven historical empty wake scopes suppressed and useful closed wake scopes folded.

### Deployment

- `[x]` Deploy Cortex.
- `[x]` Run health checks and inspect Cortex logs for prepare/render.
- `[x]` Capture before/after LLM input excerpt.

Evidence:

- `./deploy cortex` → Cortex synced and all backend services restarted.
- `./deploy status` → Entangled, Gateway, Business, Device, Queue, Storage-A, Cortex healthy; Workers `8`; Relay active.
- Cortex log lines included:
  - `suppressed empty unanchored closed scope_id=... name=user conversation`
  - `folded unanchored closed scope_id=... name=user conversation`
  - `prepared 6 messages` / `prepared 8 messages` during the live wake.

### GitHub / Commit

- `[x]` Commit implementation, tests, and this ticket update as one PR-sized commit.
- `[x]` Commit message should reference PR-73.
- `[x]` PR description must include render examples, tests, smoke, and deploy evidence.

Evidence:

- Cortex submodule commit: `d189972 cortex: suppress empty folded scope summaries`.
- Parent repo commit: this ticket update and submodule bump.

## Out of Scope

- Summary generation itself.
- Old data migration beyond display policy.
