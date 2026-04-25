# PR-61 — `subagent_report` must not be exposed to agents that cannot validly call it

| Field | Value |
|---|---|
| **Ticket** | PR-61 |
| **Status** | `[✓]` 2026-04-25 — implemented, tested, deployed |
| **Opened** | 2026-04-25 |
| **Owner** | __ |
| **Severity** | P1 tool-contract correctness — a tool is exposed in contexts where its own description says it is invalid. |
| **Blocks** | Clean main-agent/subagent capability separation. |
| **Blocked by** | — |
| **Invariant** | A tool visible in `tools[]` should be callable by the current agent role, or the call schema should not include it. |

## Bug

The latest main-agent LLM call exposes `subagent_report` in `tools[]`, but the tool description says:

```text
Report results from SubAgent to parent Agent. Only available for Sub SubAgents (subagent_id starts with 'sub-').
```

The current conversation is the main agent's user-facing turn, not a child subagent reporting upward.

## Evidence

Source: user-provided LLM request snapshot on 2026-04-25 15:37 Asia/Shanghai.

`subagent_report` is present in the same schema as `chat_reply`, `shell`, and `skill_end` for the main interaction.

## Impact

- The model can choose an invalid reporting path instead of replying to the user.
- Tool affordances differ from runtime authority.
- Subagent-only behavior leaks into main-agent reasoning.

## Acceptance Criteria

- Main-agent LLM calls do not expose subagent-only reporting tools.
- Child subagent calls that need to report upward still expose the correct reporting capability.
- Generated tool lists are role-aware in snapshot tests.

## Out of Scope

This ticket intentionally does not specify a repair method.
