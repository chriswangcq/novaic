# PR-69 — Retire `<PREV_SCOPE_HISTORY>` / `<PREV_SCOPE_TAIL>` from the main LLM path

| Field | Value |
|---|---|
| **Ticket** | PR-69 |
| **Status** | `[✓]` |
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

- [x] Add Runtime prompt assembly tests proving legacy history/tail blocks are absent in the new default path.
- [x] Add tests proving folded wake child summaries still appear through agent-root DFS assembly.
- [x] Keep or update legacy-flag tests if a compatibility path remains.

Evidence:

- `cd novaic-agent-runtime && pytest -q` → `242 passed in 0.97s`
- Targeted PR-69/legacy tests → `50 passed in 0.17s`

### Smoke Tests

- [x] Run a fresh 小牛 wake after PR-67/68.
- [x] Inspect the actual LLM request and assert no `<PREV_SCOPE_HISTORY>` / `<PREV_SCOPE_TAIL>`.
- [x] Verify previous wake information is still present as a folded scope summary.

Evidence:

- `/opt/novaic/data/backups/pr69_retire_prev_scope_blocks_smoke_20260425_190318.log`
- Smoke assertions passed: `legacy_tail_default_enabled=False`, `legacy_history_default_enabled=False`, `session_init_legacy_bridge_calls=0`, `dfs_summary_present=PR69_PRIOR_WAKE_FOLDED_SUMMARY`

### Deployment

- [x] Deploy Runtime services.
- [x] Capture online LLM request evidence and metrics/logs showing legacy injection is inactive.
- [x] Confirm rollback flag behavior if retained.

Evidence:

- `./deploy runtime` → all backend services restarted, runtime deployed.
- `./deploy status` → all ports healthy, `Workers: 8`.
- Follow-up PR-74 removed the legacy summary splice flags entirely. `WAKE_PREV_SCOPE_TAIL_ENABLED=1` remains diagnostics-only.

### GitHub / Commit

- [x] Commit cleanup, tests, and docs together.
- [x] PR description must include the LLM request excerpt proving the legacy blocks are gone.

## Out of Scope

- Deleting all old endpoint code in the same PR.
- Long-term compaction of the agent root timeline.
