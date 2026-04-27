# PR-72 — Align prompt and tool contract with agent-root continuity

| Field | Value |
|---|---|
| **Ticket** | PR-72 |
| **Status** | `[ ]` |
| **Opened** | 2026-04-27 |
| **Owner** | __ |
| **Severity** | P1 contract drift — prompt still mixes agent-root semantics with retired `<PREV_SCOPE_*>` and impossible tool guidance. |
| **Blocks** | PR-73 |
| **Blocked by** | PR-70 and PR-71 recommended. |
| **Invariant** | The LLM prompt must describe only the current continuity path and only tools actually available in the current call. |

## Intent

Remove prompt/tool drift introduced while moving from R9 prompt-layer continuity to Cortex agent-root DFS continuity.

The model should understand that cross-wake continuity comes from the agent-root scope tree and folded wake summaries, not from `<PREV_SCOPE_HISTORY>` / `<PREV_SCOPE_TAIL>` or forced root `skill_end`.

## Required Behavior

- System prompt no longer mentions `<PREV_SCOPE_HISTORY>` or `<PREV_SCOPE_TAIL>` in the main path.
- Prompt says closed wake scopes are folded as summaries under agent-root.
- Prompt does not instruct the model to use unavailable persistence APIs.
- No-tool warning does not force unrelated tools such as `shell` or `skill_begin`.
- Tool descriptions do not tell the model to close root/meta scopes that the tool will reject.

## Acceptance Criteria

- Fresh LLM calls contain no `<PREV_SCOPE_HISTORY>` / `<PREV_SCOPE_TAIL>` wording.
- No-tool retry warning only asks the model to call an appropriate real tool, usually `chat_reply`.
- Active-stack guidance is accurate for child scopes and does not invite invalid root close behavior.
- Existing prompt assembly tests still pass with updated expectations.

## Engineering Checklist

### Unit Tests

- `[ ]` Runtime prompt test: main system prompt contains agent-root continuity wording and no legacy PREV tokens.
- `[ ]` Runtime warning test: no-tool warning does not mention forced `shell`, `skill_begin`, or root `skill_end`.
- `[ ]` Tool-schema test: root/meta close guidance matches actual Cortex behavior.

### Smoke Tests

- `[ ]` Inspect a fresh 小牛 LLM request and confirm prompt contract is coherent.
- `[ ]` Trigger no-tool retry and confirm warning text is minimal and accurate.
- `[ ]` Confirm normal `chat_reply` still works.

### Deployment

- `[ ]` Deploy Runtime / Business prompt source if touched.
- `[ ]` Run health checks.
- `[ ]` Capture LLM request excerpts for prompt and warning text.

### GitHub / Commit

- `[ ]` Commit implementation, tests, and this ticket update as one PR-sized commit.
- `[ ]` Commit message should reference PR-72.
- `[ ]` PR description must include prompt excerpts and test output.

## Out of Scope

- Reintroducing legacy prompt blocks.
- User profile prompt redesign.
