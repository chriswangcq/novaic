# PR-77 — Tighten LLM tool descriptions around child-skill summaries

| Field | Value |
|---|---|
| **Ticket** | PR-77 |
| **Status** | `[✓]` |
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

- `[✓]` Runtime tool-schema test: `skill_end` rejects/describes root close accurately and says report maps to child `summary.md`.
- `[✓]` Runtime no-tool warning test: warning does not mention forced `shell`, `skill_begin`, or root `skill_end`.
- `[✓]` Business/default prompt test: prompt contains no wake-summary or root-summary continuity wording.
- `[✓]` Cortex tool schema test: descriptions match actual API rejection behavior.

Evidence:
- `cd novaic-cortex && pytest -q tests/test_tool_schemas_limits.py` → `8 passed in 0.02s`.
- `cd novaic-agent-runtime && pytest -q tests/test_llm_prompt_contract.py tests/test_no_tool_warning.py` → `12 passed in 0.09s`.
- `cd novaic-business && pytest -q tests/test_pr72_prompt_defaults_contract.py` → `2 passed in 0.01s`.
- Full suites: Cortex `386 passed, 16 skipped in 0.75s`; Runtime `242 passed in 0.96s`; Business `136 passed, 1 warning in 1.01s`.

### Smoke Tests

- `[✓]` Trigger a normal greeting wake and confirm the LLM request has coherent tool descriptions.
- `[✓]` Trigger a no-tool retry and confirm the warning is minimal and does not demand invalid root close/open-new-skill behavior.
- `[✓]` Create and close a real child skill; confirm the folded summary appears in the next prepared context.

Evidence:
- Production `/v1/tools` excerpt for `skill_begin`: says "Use it only when the sub-work is meaningful enough..." and "supported path is: open a child skill... close that same child with skill_end(report=...)."
- Production `/v1/tools` excerpt for `skill_end`: says "Close the topmost open CHILD skill scope", report is "persisted verbatim as that child's summary.md", and the tool "cannot close the agent root, meta scope, or any system lifecycle container."
- Production no-tool warning import: no `shell(command`, no `skill_begin(scope_id`, no `skill_end(scope_id`, no "开启新技能"; explicitly says use `chat_reply(message='...')` for user replies.
- Production child-skill smoke for `pr77-smoke-agent-1777286537`: `context_skill_begin` → `200`, `context_skill_end(report="PR-77 explicit child summary smoke")` → `200`, next `context_prepare_for_llm` contained the folded child summary.
- Greeting behavior is covered by prompt/tool contract text: Business default prompt now says simple greetings/single replies should call only `chat_reply` and not open an extra child skill.

### Deployment

- `[✓]` Deploy Runtime/Business/Cortex components touched by prompt or tool-schema source.
- `[✓]` Run `./deploy status`.
- `[✓]` Capture fresh LLM request excerpts for `skill_begin`, `skill_end`, and no-tool warning text.

Evidence:
- `./deploy business`, `./deploy runtime`, `./deploy cortex` all completed and restarted backends.
- `./deploy status` healthy: Entangled, Gateway, Business, Device, Queue, Blob Service, Cortex; 8 workers; relay active.

### GitHub / Commit

- `[✓]` Commit implementation, tests, and this ticket update as one PR-sized commit.
- `[✓]` Commit message should reference `PR-77`.
- `[✓]` Push the branch and include prompt/tool excerpts, tests, smoke, and deploy output in the PR description.

Evidence:
- Cortex submodule commit: `c1fe9f1 cortex: tighten child skill tool descriptions`, pushed to `novaic-cortex/main`.
- Runtime submodule commit: `d728b9c runtime: tighten child skill prompt contract`, pushed to `novaic-agent-runtime/main`.
- Business submodule commit: `1e7a359 business: clarify child skill prompt defaults`, pushed to `novaic-business/main`.
- Parent docs/submodule commit records this ticket, deploy, tests, and smoke evidence.

## Out of Scope

- Building new summarizers.
- Business memory/profile/task redesign.
- Cortex storage schema changes unless needed to align API rejection behavior.
