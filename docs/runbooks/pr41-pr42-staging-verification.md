# PR-41 Staging Verification

Covers:

- **PR-41** — `AGENT_REPLY` (and all non-trigger types) no longer stuck in `lifecycle='pending'`; HealthWorker no longer re-dispatches them as "orphans".
- The retired PR-42 continuity experiment is not part of this runbook.

Tickets: `docs/roadmap/tickets/PR-41-*.md`.

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
  AND type NOT IN ('USER_MESSAGE','SUBAGENT_SEND')
GROUP BY type;
```

Expected: empty result set.

### 4b. HealthWorker metrics

Grep runtime log for the orphan-recovery path; it should only ever carry `USER_MESSAGE` / `SUBAGENT_SEND`:

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

## 5. Success criteria

- Orphan sweep returns 0 pending non-trigger rows after 30 min idle
- Zero `AGENT_REPLY`-driven wake-ups in a 30 min idle window
- Fresh `AGENT_REPLY` rows born `consumed`

## 6. Rollback

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

Synthetic DB with 3× `AGENT_REPLY pending`, 1× `SYSTEM_NOTE pending`, 1× `USER_MESSAGE pending`, 1× `USER_MESSAGE consumed`, 1× `SUBAGENT_SEND pending`:

- Pre-PR41 orphan query surfaced 6 rows (self-loop source).
- Post-PR41 orphan query surfaces 2 rows (`USER_MESSAGE` + `SUBAGENT_SEND`), exactly the ones that should wake an agent.
- Migration flipped only the 3 `AGENT_REPLY` + 1 `SYSTEM_NOTE`, left `USER_MESSAGE pending` and `SUBAGENT_SEND pending` alone, stamped `lifecycle_updated_at` on touched rows, dropped a `.backup_before_pr41_<ts>` file.
- CI sync lint passes.
- 30 PR-41 unit tests + 29 PR-42 unit tests all green.
