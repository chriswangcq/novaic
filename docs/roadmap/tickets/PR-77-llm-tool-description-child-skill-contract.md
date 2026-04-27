# PR-77 — Tighten LLM tool descriptions around child-skill summaries

| Field | Value |
|---|---|
| **Ticket** | PR-77 |
| **Status** | `[ ]` |
| **Opened** | 2026-04-27 |
| **Owner** | __ |
| **Severity** | P1 behavior drift — incorrect tool descriptions can make the model close root/meta scopes or invent memory writes. |
| **Blocks** | Stable agent-root UX. |
| **Blocked by** | PR-74 preferred |
| **Invariant** | Tool descriptions should guide the model into the single supported path: open child skill when useful, close that child with `skill_end(report=...)`, and let Cortex fold that child summary in future DFS context. |

## Intent

Use tool descriptions and prompt contract text to shape agent behavior without adding another memory system.

The model should not be told to close root/meta/wake lifecycle scopes for continuity, and it should not be told that `skill_end` is a general memory-write API. `skill_end.report` is only the closed child scope's `summary.md`.

## Required Behavior

- `skill_begin` description says it opens a child scope only for meaningful sub-work, not for one-shot replies.
- `skill_end` description says it closes only an actually open child scope; it rejects root/meta lifecycle containers.
- `skill_end.report` description says the report is persisted verbatim as that child scope's `summary.md`.
- No-tool retry warning must not force unrelated tools (`shell`, `skill_begin`, or root `skill_end`).
- System prompt must not describe wake summary, root summary, profile memory, or chat-reply memory as Cortex behavior.

## Acceptance Criteria

- Fresh LLM call tool schema reflects child-skill-only `skill_end` semantics.
- Fresh no-tool retry warning asks for the appropriate missing action without mandating invalid tool calls.
- The model is not prompted to create a new skill after every failed/no-tool turn.
- A simple user greeting results in a single `chat_reply`, not extra skill churn.

## Engineering Checklist

### Unit Tests

- `[ ]` Runtime tool-schema test: `skill_end` rejects/describes root close accurately and says report maps to child `summary.md`.
- `[ ]` Runtime no-tool warning test: warning does not mention forced `shell`, `skill_begin`, or root `skill_end`.
- `[ ]` Business/default prompt test: prompt contains no wake-summary or root-summary continuity wording.
- `[ ]` Cortex tool schema test: descriptions match actual API rejection behavior.

### Smoke Tests

- `[ ]` Trigger a normal greeting wake and confirm the LLM request has coherent tool descriptions.
- `[ ]` Trigger a no-tool retry and confirm the warning is minimal and does not demand invalid root close/open-new-skill behavior.
- `[ ]` Create and close a real child skill; confirm the folded summary appears in the next prepared context.

### Deployment

- `[ ]` Deploy Runtime/Business/Cortex components touched by prompt or tool-schema source.
- `[ ]` Run `./deploy status`.
- `[ ]` Capture fresh LLM request excerpts for `skill_begin`, `skill_end`, and no-tool warning text.

### GitHub / Commit

- `[ ]` Commit implementation, tests, and this ticket update as one PR-sized commit.
- `[ ]` Commit message should reference `PR-77`.
- `[ ]` Push the branch and include prompt/tool excerpts, tests, smoke, and deploy output in the PR description.

## Out of Scope

- Building new summarizers.
- Business memory/profile/task redesign.
- Cortex storage schema changes unless needed to align API rejection behavior.
