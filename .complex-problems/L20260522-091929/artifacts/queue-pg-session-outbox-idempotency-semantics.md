# Queue Postgres Session/Outbox/Idempotency Replay Map

## Scope

Artifact for P016 / T012. This maps Queue Session Coordinator, durable outbox, and task idempotency replay behavior from SQLite to Postgres implementation rules.

This artifact is design-only. It does not change runtime code or production data.

## Source Evidence

- Session dispatch/finalize/rebuild:
  - `session_repo.py` `dispatch`: lines 122-395
  - `_queue_start_wake_transition`: lines 397-500
  - `session_ended`: lines 502-678
  - `rebuild`: lines 680-695
  - `_record_session_transition_after_transaction`: lines 833-846
  - `_record_attach_request_after_transaction`: lines 854-987
  - `_append_input_event_in_current_transaction`: lines 989-1010
  - pending projection helpers: lines 1023-1067
- Session ledger:
  - `append_input_received`: `session_ledger.py` lines 192-230
  - `record_input_consumed`: lines 250-305
  - generation helpers: lines 458-483
  - outbox helpers: lines 514-543
- Outbox:
  - `session_outbox.py` `drain_pending`, `publish_effect`, `_publish_and_ack`, `_mark_failed`: lines 58-135
  - `saga_repo.py` `drain_pending_effects`: lines 1217-1262
  - generic outbox list/mark methods in `fsm/sqlite_store.py`: lines 372-438
- Task idempotency:
  - `queue_db.py` `acquire_idempotency_execution`: lines 859-952
  - `complete_idempotency_execution`: lines 954-1003
  - `release_idempotency_execution`: lines 1005-1027
- Live inventory:
  - `tq_saga_outbox=6`
  - `tq_session_outbox=31`

## Design Principles

- Session state is the serialization key for dispatch/finalize decisions.
- Session inbox events are append-only authority for input durability.
- Session pending projection is diagnostic/derived; failure to write it must not undo an already durable input/session transition.
- Outbox rows are durable authority for side effects. External publication happens after the transition that created the outbox row.
- Task idempotency rows are durable execution guards and must be locked by `idempotency_key`.
- Use database-level rules for replay safety. Do not rely on process-local SQLite global locks.

## Session Row Lock Rule

SQLite uses a global process-local lock for dispatch and finalization. In Postgres, `tq_session_state` must be the per-session lock target.

Problem: a brand-new session has no state row, so there is no row to lock.

Required PG rule:

```sql
INSERT INTO tq_session_state (
  session_key, state, generation, agent_id, subagent_id, user_id, updated_at
) VALUES (
  $session_key, 'no_active', 0, $agent_id, $subagent_id, $user_id, $now
)
ON CONFLICT (session_key) DO NOTHING;

SELECT *
FROM tq_session_state
WHERE session_key = $session_key
FOR UPDATE;
```

All dispatch, attach, finalization, and pending projection decisions that depend on current session state must run after this lock. Advisory locks are not needed for normal per-session operations if this row-exists-first rule is implemented.

## Session Dispatch Mapping

### Input Durability

Current behavior:

- `dispatch` appends `INPUT_RECEIVED` first inside the transaction.
- The event can carry an idempotency key via `session_event_key(INPUT_RECEIVED, idempotency_key)`.

Postgres transaction:

1. Ensure and lock `tq_session_state` row for `session_key`.
2. Insert `INPUT_RECEIVED` into `tq_session_events` using event idempotency conflict behavior from the generic FSM store.
3. Read unconsumed inputs for the session inside the same transaction when deciding start/buffer/recovery.

If the input event idempotency key already exists, return/reuse the existing event id and do not create duplicate input rows.

### Start Wake

Current behavior:

- If no active session, Queue records a session transition to `starting`, creates a `create_wake_saga` session outbox row, and returns `wake_start_queued`.
- In some paths this happens in the initial transaction; in recovery/no-active paths it happens in a second transaction after re-reading generation.

Postgres rule:

- Both the initial and second-transaction path must use the session row lock.
- Record transition event, upsert session state to `starting`, and insert session outbox row in one transaction.
- If the required outbox row is not inserted because the transition event idempotency key already existed, return the existing outbox id if available; otherwise treat it as a replay/blocker and do not claim a new start happened.

### Buffer

Current behavior:

- If active or occupied state cannot accept attach, the input remains unconsumed and Queue records a buffered transition plus pending projection.

Postgres rule:

- With session row locked, append buffered transition event/state and pending projection.
- Do not consume the input event.
- Pending projection remains derived; failure to record projection should be logged but must not roll back input durability unless it happens in the same authoritative transition and the code elects to keep current behavior.

### Attach

Current behavior:

- Active session detection happens in the first transaction.
- Actual attach request is recorded after transaction, and it rechecks active saga/scope before creating an outbox row.
- If active session changed, input is buffered instead.

Postgres rule:

- The after-transaction attach path must ensure and lock `tq_session_state` again.
- Revalidate `active_saga_id` and `active_scope_id`.
- If they changed, record buffered transition and leave input unconsumed.
- If still active, create `publish_attach_input` outbox row and mark input consumed in the same transaction.

### Suspected-Dead Recovery

Current behavior:

- When a suspected-dead event matches active scope, session state moves to `suspected_dead`, pending projection is built, and a later wake start can include recovery archive effect.

Postgres rule:

- Lock session state.
- Insert suspected-dead-observed event and update session state in one transaction.
- Recovery archive outbox effect must be created in the same transaction as the subsequent restart/start transition that references it.

## Session Finalize Mapping

Current behavior:

- `session_ended` runs a global transaction.
- It records finalization or rejection.
- It builds pending input projection.
- If no pending input remains, records session closed/no_active.
- If pending input exists, records restart pending and creates a required `create_wake_saga` outbox row.

Postgres transaction:

1. Ensure and lock `tq_session_state(session_key)`.
2. Decide finalization from locked generation and active scope.
3. If rejected, record finalize rejected event and return.
4. Record finalized event.
5. Lock unconsumed input events for that session when building restart source:
   ```sql
   SELECT *
   FROM tq_session_events
   WHERE session_key = $session_key
     AND event_type = 'input_received'
     AND consumed_at IS NULL
   ORDER BY created_at, id
   FOR UPDATE;
   ```
6. If no pending input, record session closed/no_active.
7. If pending input exists, record restart pending, create outbox row, and update pending projection in the same transaction.

Session input during finalization:

- If dispatch locks first, its input event is visible to finalization and can be considered for restart.
- If finalization locks first and closes/restarts, dispatch runs afterward against the new state and either starts, attaches, or buffers according to the same FSM rules.

## Session Rebuild Mapping

Current behavior:

- On Queue Service startup, rebuild marks active states no_active and then projects active sessions from running/launched sagas.

Postgres rule:

- Rebuild must be single-run per Queue Service boot cluster. Use one of:
  - deployment guarantee: one queue-service process performs rebuild before accepting traffic, or
  - `pg_advisory_xact_lock(hashtext('queue_session_rebuild'))`.
- Within the rebuild transaction:
  - Lock active `tq_session_state` rows to be marked no_active.
  - Read active saga state rows.
  - Upsert rebuilt session state.
- Do not run rebuild concurrently with live dispatch traffic unless the implementation proves session row locks serialize all affected keys.

## Outbox Mapping

Current behavior:

- Generic store lists rows where `status='pending'`, ordered by `created_at, rowid`.
- Worker publishes external effect.
- On success, marks row `published` and sets `published_at`, `acked_at`, clears `last_error`.
- On failure, increments `attempts`, leaves `pending` until max attempts, then marks `dead_letter`.

Postgres-safe rule:

Pending selection must claim rows before publishing. There are two acceptable implementation choices:

1. Add outbox lease fields:
   - `claimed_by`
   - `claim_until`
   - optional `claim_token`
2. Or introduce status `publishing` with enough owner/timeout metadata to recover abandoned claims.

Preferred PG pattern:

```sql
WITH claimed AS (
  SELECT id
  FROM <outbox_table>
  WHERE status = 'pending'
    AND <effect_type/session_or_machine_filter>
  ORDER BY created_at, id
  FOR UPDATE SKIP LOCKED
  LIMIT $limit
)
UPDATE <outbox_table> o
SET status = 'publishing',
    claimed_by = $worker_id,
    claim_until = $now + $lease_interval,
    updated_at = $now
FROM claimed
WHERE o.id = claimed.id
RETURNING o.*;
```

Then publish outside the transaction.

On success:

```sql
UPDATE <outbox_table>
SET status = 'published',
    published_at = COALESCE(published_at, $now),
    acked_at = COALESCE(acked_at, $now),
    last_error = NULL,
    claim_until = NULL,
    claimed_by = NULL,
    updated_at = $now
WHERE id = $id
  AND status = 'publishing'
  AND claimed_by = $worker_id;
```

On failure:

- Increment attempts.
- Return to `pending` if attempts remain.
- Move to `dead_letter` when attempts reach max.
- Clear claim metadata.

If implementation refuses to add claim metadata, P014 must enforce exactly one worker per outbox table/effect type during PG runtime. That is weaker and should be treated as an operational constraint, not a database guarantee.

### Publish-Before-Ack Crash

If external publish succeeds and process crashes before ack:

- Row remains `publishing` until `claim_until`, then becomes claimable again.
- Republish must be safe through the outbox row `idempotency_key` and downstream idempotency.
- This matches current durable-outbox intent, but PG implementation must make retry explicit.

### Ack Retry Race

If two workers try to ack the same row:

- Only the worker holding the current claim can update from `publishing` to `published`.
- A stale worker update affects zero rows and must not report success.

## Task Idempotency Ledger Mapping

Current behavior:

- Missing idempotency key returns `acquired` without writing.
- Acquire inserts `in_progress` with owner, task, lease_until.
- Completed rows return `completed` with parsed result.
- Active in-progress row owned by another owner increments contention and returns `in_progress`.
- Expired in-progress or same owner updates ownership/lease and returns `acquired`.
- Complete first tries predicate update by key/status/owner/task; if that fails, it upserts completed.
- Release deletes in-progress row only if key/status/owner/task matches.

Postgres transaction for acquire:

```sql
INSERT INTO tq_idempotency_ledger (
  idempotency_key, status, owner_token, task_id, result,
  contention_count, last_contended_at, lease_until, updated_at
) VALUES (
  $key, 'in_progress', $owner, $task_id, NULL, 0, NULL, $lease_until, $now
)
ON CONFLICT (idempotency_key) DO NOTHING;

SELECT *
FROM tq_idempotency_ledger
WHERE idempotency_key = $key
FOR UPDATE;
```

Then:

- If status is `completed`, return completed result.
- If status is `in_progress`, lease active, and owner differs, increment contention and return `in_progress`.
- Otherwise update owner/task/lease_until/updated_at and return `acquired`.

Postgres transaction for complete:

- Preserve current API behavior initially:
  1. `UPDATE ... WHERE idempotency_key=$key AND status='in_progress' AND owner_token=$owner AND task_id=$task_id`.
  2. If no row updated, `INSERT ... ON CONFLICT (idempotency_key) DO UPDATE SET status='completed', owner_token=excluded.owner_token, task_id=excluded.task_id, result=excluded.result, lease_until=NULL, updated_at=excluded.updated_at`.
- This means a late complete can overwrite an existing key's completed result, matching current SQLite behavior. If product wants stricter semantics, that must be a separate behavior-change ticket.

Postgres transaction for release:

- `DELETE FROM tq_idempotency_ledger WHERE idempotency_key=$key AND status='in_progress' AND owner_token=$owner AND task_id=$task_id`.
- Return true iff a row was deleted.

## Live Pending Outbox Cutover Requirement

P012 found live pending rows:

- `tq_saga_outbox=6`
- `tq_session_outbox=31`

P014 must choose one of two safe cutover paths:

1. Drain before migration:
   - Stop producers.
   - Let outbox workers drain to zero.
   - Verify zero pending/dead-letter policy.
   - Migrate only final statuses.
2. Migrate pending rows:
   - Stop SQLite writers and outbox workers.
   - Copy pending/published/dead-letter rows with idempotency keys and attempt counters.
   - Start only PG-backed outbox workers.
   - Ensure no SQLite outbox worker remains running.

Do not run SQLite and PG outbox workers against copied rows at the same time.

## Crash-Window Outcomes

Publish succeeds before ack:

- Outbox remains claimable after claim lease expiry and republishes using idempotency key.
- If downstream already performed the side effect, downstream idempotency returns existing result or no-op.

Ack succeeds then worker crashes:

- Row is `published`, later drain skips it.

Failure mark races retry:

- Claim owner predicate makes stale failure updates affect zero rows after another worker has reclaimed the row.

Duplicate idempotency key during in-progress work:

- Row lock serializes contenders.
- Active lease and different owner returns `in_progress` and increments contention.

Session input during finalization:

- Session row lock serializes dispatch and finalization.
- Input is either seen by finalization's pending projection or appended after finalization and handled under the new session state.

Attach races session state change:

- Attach path re-locks session state and revalidates saga/scope before creating outbox. If changed, it buffers instead.

## Implementation Blockers

- Generic outbox tables currently lack claim/lease columns. PG-safe multi-worker outbox draining needs schema changes or a strict single-worker deployment constraint.
- Session state must be made row-present before locking. Implementation must add an explicit "ensure session row" helper.
- Rebuild needs a single-run lock/operational guarantee before multiple queue-service processes can start concurrently.
- `complete_idempotency_execution` currently allows fallback upsert to completed even after predicate update misses. Preserving this is API-compatible but semantically loose; changing it requires a separate decision.
- P017 must still define timestamp types and PG exception retry/defer behavior.

## P014 Inputs

- Stop SQLite queue producers and outbox workers before copying live outbox rows.
- Decide drain-before-migrate versus migrate-pending-rows.
- Add or operationally constrain outbox claim behavior before running more than one PG outbox worker.
- Smoke tests must cover dispatch start, dispatch attach, session-ended restart, outbox publish/ack retry, idempotency duplicate completed, and idempotency in-progress contention.

