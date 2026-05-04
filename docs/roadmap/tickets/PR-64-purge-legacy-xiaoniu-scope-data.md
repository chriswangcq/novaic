# PR-64 — Purge legacy 小牛 scope/runtime data before agent-root rollout

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


| Field | Value |
|---|---|
| **Ticket** | PR-64 |
| **Status** | `[✓]` 2026-04-25 — operational cleanup completed |
| **Opened** | 2026-04-25 |
| **Owner** | __ |
| **Severity** | P0 data hygiene — old archived summaries directly pollute new continuity tests. |
| **Blocks** | PR-65+, clean validation of agent-root continuity. |
| **Blocked by** | User authorization to delete old data. |
| **Invariant** | New continuity tests must not read pre-agent-root archived summaries or runtime state. |

## Intent

Delete the target 小牛 agent's legacy Cortex/runtime data instead of migrating it.

Target known from investigation:

- `user_id = 155cc065-d462-413d-a60c-406b64a8bc84`
- `agent_id = 415f6cfd4e5b4a04911b66cb8ab2cad7`

## Scope

Delete or reset:

- Cortex `/ro/active/*` for this agent.
- Cortex `/ro/scopes/*` and `/ro/scopes/_index.jsonl` for this agent.
- Runtime active session rows for this agent/subagent.
- Subagent fields that point to old scope continuity anchors, including `last_scope_id` / `last_scope_archived_at` if present.
- Any queued/running wake sagas tied to deleted scopes.
- Entangled `chat_messages`, `message_outbox`, and message transition rows for this agent, so IM replay cannot rehydrate old conversation history.

## Acceptance Criteria

- Fresh 小牛 wake starts with no legacy `<PREV_SCOPE_HISTORY>` entries.
- No active session references a deleted scope.
- Cortex scope list for the target agent contains only newly-created agent-root-era scopes after PR-65+ starts writing them.
- Deletion command output is captured in the PR/deploy notes.

## Engineering Checklist

### Unit Tests

- No product-code behavior is expected to change in this ticket.
- Run the narrow tests that guard Cortex scope-list/tail read behavior if any cleanup helper code is introduced.
- If this ticket remains operational-only, record "N/A — data cleanup only" in the completion notes.

### Smoke Tests

- Before cleanup: capture archived scope summary count and active scope count for the target agent.
- After cleanup: verify archived scope summaries are empty, active scopes are empty, and no runtime active session points at a deleted scope.
- Verify old `chat_messages` / `message_outbox` rows for this agent are gone.
- Trigger or inspect the next 小牛 wake only after PR-65+ is available; PR-64 alone is allowed to leave the agent with no Cortex history.

### Deployment

- This ticket is an operations deployment, not a code deployment.
- Run cleanup against production only after confirming target `user_id` and `agent_id`.
- Capture command transcript or summarized output in this ticket.

### GitHub / Commit

- Commit the ticket/documentation change separately from runtime implementation tickets.
- If an operational script is added, include it in the same PR and document the exact command used.

## Out of Scope

- No backfill.
- No summary migration.
- No user profile migration.

## Rollback

No semantic rollback. If a backup is taken operationally, it is for emergency forensic restore only, not part of the new design.

## Completion Notes

Executed on production at `2026-04-25T17:55:29+08:00`.

Target:

- `user_id = 155cc065-d462-413d-a60c-406b64a8bc84`
- `agent_id = 415f6cfd4e5b4a04911b66cb8ab2cad7`
- `subagent_id = main-415f6cfd`

Operational log:

- `/opt/novaic/data/backups/pr64_xiaoniu_cleanup_20260425_175529.log`

### Unit Tests

N/A — this ticket performed targeted production data cleanup only. No product code was changed.

### Smoke Evidence

Before cleanup:

- `chat_messages = 8`
- `message_outbox = 4`
- `message_state_transitions = 8`
- `queue sagas = 17`
- `queue tasks = 112`
- `queue idempotency ledger rows by task = 112`
- Cortex OSS objects under target agent prefix = `33`
- `subagents.last_scope_id = 1d066205-ed01-4a46-9e3a-2f0cec75569b`

After cleanup:

- `chat_messages = 0`
- `message_outbox = 0`
- `message_state_transitions = 0`
- `queue active_sessions = 0`
- `queue pending_triggers = 0`
- `queue sagas = 0`
- `queue tasks = 0`
- `queue idempotency ledger rows by task = 0`
- Cortex OSS objects under target agent prefix = `0`
- `subagents.current_scope_id`, `last_scope_id`, and `last_scope_archived_at` cleared.

Cortex API smoke:

- `POST /v1/scope/list_summaries` returned `{"entries": []}`.
- `POST /v1/scope/read_tail` for old scope ids `826384a8...`, `0ea555ae...`, `90a6f7c...`, and `1d066205...` returned `meta.found=false`.

### Deployment

N/A — operational cleanup only. No service restart was required.

### GitHub / Commit

This ticket should be committed with the agent-root design/ticket documentation update.
