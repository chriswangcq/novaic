# Session Harness Ideal Gap Ledger

This ledger compares the current Queue session harness with the intended
"mathematically clean" shape:

```text
Input event
  -> durable inbox/event append
  -> explicit state snapshot
  -> pure FSM/reducer decision
  -> atomic state/event/outbox write
  -> durable outbox publisher
```

The agent remains the subject. User messages are environment input events.
Shell, Cortex, Queue, Saga, and IM are boundaries. The FSM must stay pure and
must not own DB/Queue/Saga/Cortex dependencies.

## Current Good Shape After PR-282

- `SessionRepository` no longer owns direct saga creation.
- `SessionRepository` requires explicit `SessionLedgerRepository` and
  `SessionOutboxDispatcher`.
- `SessionOutboxDispatcher` is the single wake saga creation publisher.
- `SessionLedgerRepository` owns session state/events/pending projection/input
  consumption/outbox rows.
- Generic FSM substrate exists and session dispatch/finalize decision uses it.
- Startup rebuild is delegated to `session_rebuild.py`.
- Wake start/restart planning is delegated to `session_wake_plan.py`.
- Outbox append/publish wrappers live on `SessionOutboxDispatcher`.
- Dispatch decision traces are built next to session FSM logic.
- Full runtime suite passes after the cutover.

## Closed Gaps In This Pass

### GAP-1: Ideal/current map is not a single durable ledger

The design exists across tickets and code, but there is no one file naming the
remaining executable gaps after PR-277. This makes future cleanup easy to
forget or duplicate.

Ticket: PR-278. Status: Closed.

### GAP-2: Startup rebuild still lives inside `SessionRepository`

`SessionRepository.rebuild()` still knows how to query `tq_sagas` and rebuild
session state. This is boundary IO and belongs in a named projector/adapter, not
inside the dispatch/finalize coordinator.

Ticket: PR-279. Status: Closed.

### GAP-3: Wake start/restart planning is still inline coordinator code

The repository still shapes saga context, recovery dispatch metadata,
idempotency keys, and create-wake outbox effects inline. This is deterministic
planning and should be a pure helper fed by explicit inputs.

Ticket: PR-280. Status: Closed.

### GAP-4: Outbox append/publish wrapper is still coordinator-owned

The repository still has helper methods that append outbox rows and normalize
publish results. The dispatcher is the outbox boundary, so this wrapper belongs
there.

Ticket: PR-281. Status: Closed.

### GAP-5: Dispatch decision trace is still repository-owned

The repository computes FSM decision trace payloads. This is deterministic
calculation and should live next to the session FSM decision logic.

Ticket: PR-282. Status: Closed.

## Residual Watchlist

- `SessionRepository` remains the application coordinator. That is intentional:
  it wires DB transactions, ledger, outbox dispatcher, FSM decision, and saga
  read adapters, but it should not regain hidden input parsing, direct saga
  creation, state row construction, or business payload shaping.
- New harness work should add stable substrate modules or pure helper modules
  instead of putting deterministic calculation back into `SessionRepository`.
- If future requirements require another state-machine family, reuse the generic
  FSM substrate rather than adding a bespoke imperative branch.

## Explicit Non-Gaps

- FSM should not directly read or write DB.
- FSM should not publish Queue tasks or create sagas.
- `SessionRepository` may remain an application coordinator, as long as it owns
  orchestration only and not hidden inputs, state storage, or side-effect
  publication.
- Saga HTTP routes are not part of the session harness migration.
