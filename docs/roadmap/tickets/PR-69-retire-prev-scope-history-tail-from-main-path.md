# PR-69 — Retire `<PREV_SCOPE_HISTORY>` / `<PREV_SCOPE_TAIL>` from the main LLM path

| Field | Value |
|---|---|
| **Ticket** | PR-69 |
| **Status** | `[ ]` |
| **Opened** | 2026-04-25 |
| **Owner** | __ |
| **Severity** | P1 cleanup — removes the prompt-layer continuity path that bypasses Cortex DFS semantics. |
| **Blocks** | Stable agent-root continuity rollout. |
| **Blocked by** | PR-67, PR-68 |
| **Invariant** | Cross-wake continuity in the main path comes from agent-root DFS assembly, not extra history/tail system blocks. |

## Intent

After agent-root wake scopes are live, remove or default-disable the old R9 prompt injection layer:

- `<PREV_SCOPE_HISTORY>`
- `<PREV_SCOPE_TAIL>`
- `previous_scope_id` as the main continuity read anchor
- `last_scope_id`-driven tail splicing

The old endpoints may remain temporarily for diagnostics or rollback, but the default LLM request must not include these blocks.

## Acceptance Criteria

- Fresh 小牛 LLM calls contain no `<PREV_SCOPE_HISTORY>` block.
- Fresh 小牛 LLM calls contain no `<PREV_SCOPE_TAIL>` block.
- The same calls still contain prior wake continuity through folded child-scope summaries under agent root.
- Metrics/logs can distinguish new agent-root continuity from legacy R9 injection.
- Legacy kill switches or compatibility flags are documented if retained.

## Engineering Checklist

### Unit Tests

- Add Runtime prompt assembly tests proving legacy history/tail blocks are absent in the new default path.
- Add tests proving folded wake child summaries still appear through agent-root DFS assembly.
- Keep or update legacy-flag tests if a compatibility path remains.

### Smoke Tests

- Run a fresh 小牛 wake after PR-67/68.
- Inspect the actual LLM request and assert no `<PREV_SCOPE_HISTORY>` / `<PREV_SCOPE_TAIL>`.
- Verify previous wake information is still present as a folded scope summary.

### Deployment

- Deploy Runtime services.
- Capture online LLM request evidence and metrics/logs showing legacy injection is inactive.
- Confirm rollback flag behavior if retained.

### GitHub / Commit

- Commit cleanup, tests, and docs together.
- PR description must include the LLM request excerpt proving the legacy blocks are gone.

## Out of Scope

- Deleting all old endpoint code in the same PR.
- Long-term compaction of the agent root timeline.
