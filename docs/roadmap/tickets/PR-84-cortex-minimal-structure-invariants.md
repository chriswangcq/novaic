# PR-84 — Add Cortex minimal-structure invariant tests

| Field | Value |
|---|---|
| **Ticket** | PR-84 |
| **Status** | `[code]` |
| **Opened** | 2026-04-28 |
| **Owner** | __ |
| **Severity** | P0 regression prevention — after cleanup, the small Cortex model needs tests that protect structure without constraining LLM intelligence. |
| **Depends on** | PR-82 and PR-83 preferred, but can start in parallel if expected final names are clear. |
| **Blocks** | Confident deletion of old memory/summary compatibility paths. |
| **Invariant** | Cortex maintains structure; LLM owns meaning. Tests must verify scope mechanics, not summary content quality. |

## Background

The desired implementation is "structure less, intelligence more":

```text
Cortex: LIFO scope tree, active stack, summary.md, DFS context
LLM: decides content and writes report when closing a scope
Runtime: lifecycle and tool execution
```

Tests should not enforce a summary schema or require specific facts. They should only enforce that the structural carrier behaves correctly.

## Goal

Add invariant tests for the minimal Cortex structure:

- active scopes remain expanded;
- closed scopes fold to `summary.md`;
- `skill_end(report)` persists the report verbatim;
- LIFO stack rules are enforced;
- agent root cannot be closed by LLM;
- DFS context order is stable.

## Non-Goals

- Do not test that a summary contains a specific user fact.
- Do not enforce a fixed report template.
- Do not introduce automatic summary generation.
- Do not add user profile or memory extraction.

## Implementation Checklist

### 1. Scope close persistence

- [x] Test that closing a child/wake scope with `report="abc"` writes exactly `abc` to that scope's `summary.md`.
- [x] Test that the report is not post-processed, prefixed, or replaced by generated text.
- [x] Test unicode/non-ASCII content is preserved when existing code supports it.

### 2. LIFO stack enforcement

- [x] Test closing the current stack top succeeds.
- [x] Test closing a non-top scope is rejected.
- [x] Test closing the agent root is rejected.
- [x] Test stack state after close matches parent scope.

### 3. Active vs folded rendering

- [x] Test active wake scope context is expanded in LLM context.
- [x] Test active nested child scope context is expanded.
- [x] Test closed child scope renders as folded summary.
- [x] Test closed child details do not leak when folded.

### 4. DFS order

- [x] Test prior closed siblings render in DFS order.
- [x] Test active branch is expanded at its DFS position.
- [x] Test system prompt ordering is stable relative to scope tree context.

### 5. Structural finalize boundary

- [x] Test structural `scope_end` used by force-finalize does not write normal summary.
- [x] Test folded summaries only appear after semantic close with report.

## Unit Test Requirements

This entire ticket is mostly unit tests. Expected areas:

- `novaic-cortex` tests for scope tree and context engine.
- `novaic-agent-runtime` tests only where Runtime calls Cortex closure APIs.
- No provider/LLM dependency in unit tests.

Required commands should include whichever are relevant after implementation:

```bash
pytest novaic-cortex/tests -q
pytest novaic-agent-runtime/tests -q
```

## Smoke Test Requirements

- [ ] Start local Cortex + Runtime stack.
- [ ] Create an agent-root scope.
- [ ] Create a wake child scope.
- [ ] Append context to wake.
- [ ] Close wake via `skill_end(report="smoke summary")`.
- [ ] Prepare next LLM context.
- [ ] Verify folded scope shows `smoke summary` and not the closed wake's raw internal context.

## Deployment Checklist

- [ ] Merge tests and any minimal code fixes.
- [ ] Deploy affected services if implementation changes were needed.
- [ ] If test-only, no service deploy is required, but CI evidence must be pasted.
- [ ] Capture evidence:
  - [ ] unit test output;
  - [ ] one local or production smoke context snippet showing folded summary.

## GitHub / Commit Checklist

- [ ] Commit subrepo changes in `novaic-cortex` and/or `novaic-agent-runtime`.
- [ ] Commit parent submodule pointer updates.
- [ ] PR description links this ticket.
- [ ] PR description explicitly states tests protect structure, not summary quality.
- [ ] PR description includes unit and smoke outputs.

## Acceptance Criteria

- Tests fail if `skill_end(report)` stops being the only normal summary writer.
- Tests fail if closed scopes expand raw details in later context.
- Tests fail if active scopes get folded early.
- Tests fail if LIFO close rules are weakened.

## Rollback

Rollback if tests depend on implementation internals too tightly and block legitimate refactors. The invariant should be behavior-level, not path-name-level.
