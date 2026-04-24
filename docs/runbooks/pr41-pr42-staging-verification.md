# PR-41 / PR-42 Staging Verification

> **2026-04-23 (PR-55)**: the PR-42 half of this runbook is **obsolete**.
> `<HANDOFF_NOTES>` / `<HISTORICAL_SUMMARY>` were phantom blocks — the
> driving tool `subagent_rest` was never in `BUILTIN_TOOL_SCHEMAS` and
> `generate_simple_summary` returned empty. Both blocks are removed.
> PR-41 sections (lifecycle) remain valid. For current wake-continuity
> verification use `scripts/canary/wake-continuity-smoke.sh` (state
> layer: `<PREV_SCOPE_TAIL>` via `previous_scope_id`). See
> `[docs/roadmap/tickets/PR-55-phantom-summary-pipeline-cleanup.md](../roadmap/tickets/PR-55-phantom-summary-pipeline-cleanup.md)`.

Covers:

- **PR-41** — `AGENT_REPLY` (and all non-trigger types) no longer stuck in `lifecycle='pending'`; HealthWorker no longer re-dispatches them as "orphans".
- ~~**PR-42**~~ — ~~wake-up scopes receive `<HANDOFF_NOTES>` + `<HISTORICAL_SUMMARY>` system messages (text-layer continuity).~~ **Retired by PR-55**; see the notice above.

Tickets: `docs/roadmap/tickets/PR-41-*.md`, `docs/roadmap/tickets/PR-42-*.md`.

---

## 0. Prerequisites on staging box

```bash
# Entangled DB location (adjust if different)
export ENTANGLED_DB=~/.novaic/data/entangled.db

# Where gateway + runtime log go
export GATEWAY_LOG=~/.novaic/logs/gateway.log
export RUNTIME_LOG=~/.novaic/logs/runtime.log
```

## 1. Deploy sequence

```bash
# pull + install
git pull --ff-only
./scripts/build-and-release.sh --staging   # or your usual deploy cmd

# stop writers before migration
systemctl stop novaic-gateway novaic-runtime
```

## 2. Run one-time cleanup (PR-41)

```bash
bash scripts/gateway/migrate_pr41_agent_reply_orphans.sh "$ENTANGLED_DB"
```

Expected output shape (proven on a synthetic DB locally):

```
=== Backing up DB ===
=== Counting affected rows ===
Pending non-trigger rows to clean up: <N>
=== Breakdown by type ===
AGENT_REPLY|<n1>
SYSTEM_NOTE|<n2>
...
=== Running migration ===
=== Verifying ===
Remaining pending non-trigger rows: 0
Migration complete.
```

Sanity check that real user messages were **not** touched:

```bash
sqlite3 "$ENTANGLED_DB" \
  "SELECT type, lifecycle, COUNT(*) FROM chat_messages GROUP BY type, lifecycle;"
```

`USER_MESSAGE|pending` count should equal what it was pre-migration.

## 3. Start services, tail logs

```bash
systemctl start novaic-gateway novaic-runtime
tail -F "$GATEWAY_LOG" "$RUNTIME_LOG"
```

## 4. PR-41 live verification (the "5 分钟自动苏醒" bug)

### 4a. No new orphans appearing for non-trigger types

After services run idle for ~15 min, the orphan-sweep SQL must return 0 rows for `AGENT_REPLY` / `SYSTEM_NOTE` / any non-trigger type:

```sql
SELECT type, COUNT(*)
FROM chat_messages
WHERE lifecycle='pending'
  AND type NOT IN ('USER_MESSAGE','SUBAGENT_SEND','SPAWN_SUBAGENT')
GROUP BY type;
```

Expected: empty result set.

### 4b. HealthWorker metrics

Grep runtime log for the orphan-recovery path; it should only ever carry `USER_MESSAGE` / `SUBAGENT_SEND` / `SPAWN_SUBAGENT`:

```bash
grep -E "orphan.*recover|TriggerType\.RECOVERED" "$RUNTIME_LOG" | tail -50
```

Expected: no `AGENT_REPLY` rows in the trigger payload.

### 4c. New `AGENT_REPLY` rows are born `consumed`

Send a user prompt, let the agent reply, then:

```bash
sqlite3 "$ENTANGLED_DB" \
  "SELECT id,type,lifecycle,lifecycle_updated_at FROM chat_messages \
   WHERE type='AGENT_REPLY' ORDER BY id DESC LIMIT 5;"
```

Every `AGENT_REPLY` row must have `lifecycle='consumed'` and a populated `lifecycle_updated_at` (the write-side fix in `entity_store.py::append`).

## 5. PR-42 live verification (wake 带 handoff + summary)

### 5a. Trigger a real wake (non-spawn)

Easiest path: let `subagent_rest` put an agent to sleep with non-empty `handoff_notes`, then fire a new `USER_MESSAGE`. Look at the `session.init` payload being built:

```bash
grep -E "session\.init.*payload|_build_session_init_payload" "$RUNTIME_LOG" | tail
```

Payload should include `handoff_notes` and `wake_reason`.

### 5b. Continuity messages injected into scope

In runtime log, after `handle_session_init` runs:

```bash
grep -E "wake_continuity|HANDOFF_NOTES|HISTORICAL_SUMMARY" "$RUNTIME_LOG" | tail
```

Expected order inside the Cortex scope initial context:

```
SYSTEM_PROMPT → <HANDOFF_NOTES> → <HISTORICAL_SUMMARY> → recall_messages…
```

### 5c. Trigger-type gating (no leak on SPAWN)

Spawn a brand-new subagent. `<HANDOFF_NOTES>` / `<HISTORICAL_SUMMARY>` must **not** appear in its init payload (controlled by `WAKE_CONTINUITY_ENABLED_TRIGGERS`).

### 5d. Size cap

Synthesise an over-large `historical_summary` (e.g. write ~16KB into `subagents.historical_summary`) then wake. The injected block should contain the `[truncated]` marker and runtime log should emit a `wake_continuity.truncated` warning / metric.

## 6. Success criteria

- Orphan sweep returns 0 pending non-trigger rows after 30 min idle
- Zero `AGENT_REPLY`-driven wake-ups in a 30 min idle window
- Fresh `AGENT_REPLY` rows born `consumed`
- Wake after rest carries `<HANDOFF_NOTES>` and `<HISTORICAL_SUMMARY>`
- Spawn does **not** carry continuity block
- Oversize summary gets `[truncated]` + metric

## 7. Rollback

If anything goes wrong, the migration made a backup:

```bash
ls -lh "${ENTANGLED_DB}.backup_before_pr41_"*
```

To revert code only (DB rows already `consumed` are safe to keep — they just won't be retried):

```bash
git revert <merge-sha>
systemctl restart novaic-gateway novaic-runtime
```

To revert DB too (rarely needed):

```bash
systemctl stop novaic-gateway novaic-runtime
cp "${ENTANGLED_DB}.backup_before_pr41_<timestamp>" "$ENTANGLED_DB"
systemctl start novaic-gateway novaic-runtime
```

## 8. Pitfalls observed during local proof

- `message_outbox` is **not** touched by migration — only `chat_messages.lifecycle`. Anything already delivered via outbox stays that way.
- The migration only flips rows where `type NOT IN (outbox_trigger_types)`. A `USER_MESSAGE` stuck pending is a **real** grievance and must keep its state so HealthWorker can still pick it up.
- `lint_outbox_trigger_sync.sh` guards against future drift between Business (`outbox_trigger_types`) and Entangled (`ORPHAN_ELIGIBLE_TYPES`). Already wired into `.github/workflows/lint.yml`.

## 9. Local dry-run I already did

Synthetic DB with 3× `AGENT_REPLY pending`, 1× `SYSTEM_NOTE pending`, 1× `USER_MESSAGE pending`, 1× `USER_MESSAGE consumed`, 1× `SPAWN_SUBAGENT pending`:

- Pre-PR41 orphan query surfaced 6 rows (self-loop source).
- Post-PR41 orphan query surfaces 2 rows (`USER_MESSAGE` + `SPAWN_SUBAGENT`), exactly the ones that should wake an agent.
- Migration flipped only the 3 `AGENT_REPLY` + 1 `SYSTEM_NOTE`, left `USER_MESSAGE pending` and `SPAWN_SUBAGENT pending` alone, stamped `lifecycle_updated_at` on touched rows, dropped a `.backup_before_pr41_<ts>` file.
- CI sync lint passes.
- 30 PR-41 unit tests + 29 PR-42 unit tests all green.

