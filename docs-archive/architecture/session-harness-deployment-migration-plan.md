# Session Harness Deployment Migration Plan

This plan covers the transition from the current session coordinator to the
durable FSM/outbox harness.

## Invariants

- User messages are environment input events.
- The agent wake is the subject; Queue, Saga, Cortex, IM, and shell are
  boundaries.
- The durable session ledger is the authority for input, state, events, and
  outbox intent.
- A wake creation request is successful only after one of these is true:
  - queued path recorded `starting` and a worker later observed wake creation.

## Migration Stages

### Stage 1: Safe State Vocabulary

Code requirements:
- `no_active`, `starting`, `active`, `ending`, `suspected_dead`, `recovering`
  are valid runtime states.
- Non-attachable lifecycle states buffer input.

Validation:
- FSM tests for every state.
- Confirm `starting` rows are not returned by active-session diagnostics.

Rollback:
- Rollback to pre-FSM code is not supported in-process. Reset or migrate the
  queue database out of band before booting older code.

### Stage 2: Durable Outbox Worker

Code requirements:
- `SessionOutboxWorker` can drain bounded batches.
- Worker has explicit dependencies and no business decision logic.
- Production startup launches the worker as a visible subprocess; it is not a
  hidden Queue Service lifespan task.

Validation:
- Worker one-shot drain test.
- Manual drain on staging:
  - list pending session outbox rows;
  - run one drain batch;
  - confirm published/failed/dead-letter counters.

Rollback:
- Stop the worker first.
- Do not run older synchronous dispatch code against the current queue DB.

### Stage 3: Queued Wake Start

Code requirements:
- Dispatch records `starting` and create-wake outbox before returning queued.
- Caller contract treats queued wake as durable acknowledgement, not live wake.
- Worker drains create-wake effects.

Validation:
- Dispatch return contract tests.
- Pending outbox retry tests.
- Health checks:
  - count `tq_session_state.state = 'starting'`;
  - count pending `create_wake_saga` outbox rows;
  - alert if either stays non-zero beyond the SLA window.

Rollback:
- Drain pending create-wake rows when possible.
- If downgrade is required, perform an explicit DB reset/export plan outside
  the runtime. The runtime no longer carries old-version schema migration or
  compatibility branches.

### Stage 4: Observed Event Reducer

Code requirements:
- Wake-created observation transitions `starting` to `active`.
- Remaining observed events are routed through the handler.
- Publisher does not directly own state mutation details.

Validation:
- Observation duplicate/stale-generation tests.
- Audit timeline must explain input event, decision, outbox effect, observation,
  and final state.

Rollback:
- Observed-event rows must match the current canonical payload contract.
- Historical compatibility key handling has been removed.

### Stage 5: Legacy Cleanup

Code requirements:
- Delete sync wake publish from dispatch.
- Delete compatibility naming and dual-path tests.
- Update docs and residue guards.

Validation:
- Grep:
  - no `publish_wake_creation_effect` call in `session_repo.py`;
  - no active `shadow:` event-key builders;
  - no stale `legacy` wording in active harness modules.
- Full runtime suite.

Rollback:
- Rollback requires an explicit DB reset/export plan; old schema versions fail
  fast at boot.

## Runtime Health Checks

- `starting_count`: sessions in `starting`.
- `active_count`: sessions in `active`.
- `pending_create_wake_outbox_count`.
- `failed_session_outbox_count`.
- `dead_letter_session_outbox_count`.
- `oldest_pending_session_outbox_age_seconds`.
- `oldest_starting_session_age_seconds`.

## Incident Audit Commands

Use read-only inspection:

```bash
sqlite3 "$QUEUE_DB" "select session_key,state,generation,active_scope_id,updated_at from tq_session_state order by updated_at desc limit 20;"
sqlite3 "$QUEUE_DB" "select id,session_key,effect_type,status,attempts,last_error,created_at from tq_session_outbox order by created_at desc limit 20;"
sqlite3 "$QUEUE_DB" "select id,session_key,event_type,generation,created_at from tq_session_events order by created_at desc limit 40;"
```

Then use the session audit helper in tests or a diagnostic script to summarize
the event stream without reimplementing FSM rules.

## Cleanup Gate

Old code may be removed only when:

- No pending create-wake outbox rows from the old path remain.
- No `starting` rows are older than the accepted worker SLA.
- Full runtime suite passes.
- Rollback plan for the exact deployment has been reviewed.
