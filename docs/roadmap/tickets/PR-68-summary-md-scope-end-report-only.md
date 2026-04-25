# PR-68 — Restore `summary.md` semantics to scope-end report only

| Field | Value |
|---|---|
| **Ticket** | PR-68 |
| **Status** | `[ ]` |
| **Opened** | 2026-04-25 |
| **Owner** | __ |
| **Severity** | P0 memory correctness — summaries are the semantic content of folded scopes. |
| **Blocks** | PR-69 |
| **Blocked by** | PR-67 |
| **Invariant** | `summary.md` equals the report supplied when the scope is closed; it is not derived from `chat_reply`. |

## Intent

Remove the current fallback that derives archived root summary text from `chat_reply.message`.

In the agent-root model, folded wake scopes should carry deliberate scope-end reports.

## Required Behavior

- `skill_end(scope_id=..., report=...)` is the normal producer for `summary.md`.
- Runtime must not convert `chat_reply` text into `summary.md`.
- If the LLM fails to close the wake scope, system auto-close may leave empty/no-report metadata, but not a fabricated summary.
- Tool descriptions and prompt text should instruct the LLM to close current wake/skill scopes with concise reports.

## Acceptance Criteria

- Unit test: `chat_reply` alone does not produce a summary body.
- Unit test: `skill_end(report="...")` writes exactly that report to `summary.md`.
- Unit test: auto-close path does not paste user-facing reply into summary.
- LLM-visible tool contract no longer says root meta summary appears as `<PREV_SCOPE_HISTORY>`.

## Engineering Checklist

### Unit Tests

- Remove or update tests that expect `chat_reply`-derived summaries.
- Add tests for `skill_end.report` precedence and exact persistence.
- Add tests for silent/auto-close behavior producing no fabricated user-facing summary.

### Smoke Tests

- Run one wake where the agent replies but does not provide a report; verify no `chat_reply` excerpt lands in `summary.md`.
- Run one wake with an explicit report; verify the folded summary equals that report.
- Inspect the resulting LLM call to ensure old summary wording is gone.

### Deployment

- Deploy Runtime/Cortex components touched by summary production.
- Capture online evidence from archived `summary.md` and the next LLM call.

### GitHub / Commit

- Commit implementation and tests together.
- PR description must call out the intentional behavior change: no automatic `chat_reply` summary fallback.

## Out of Scope

- User profile extraction.
- Automatic summarizer pass.
- Old summary migration.
