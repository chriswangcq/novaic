# Implement ContextEvent append and root initialization

## Problem Definition

The ContextEvent store can read event logs, but it cannot yet append authoritative events. P013 must add append semantics that assign generated fields from explicit providers, preserve per-stream sequence order, and initialize a fresh root stream without migrating old DFS history.

## Proposed Solution

- Extend `ContextEventStore` with injectable `clock` and `id_provider` dependencies.
- Add `append_event(...)` that:
  - reads existing events for the root stream;
  - assigns `seq = len(existing) + 1`;
  - assigns `event_id` and `occurred_at` using injected providers;
  - builds and validates a `ContextEvent`;
  - appends one JSON line through Workspace system IO.
- Add `initialize_root(...)` that appends `RootInitialized` for a fresh root stream with explicit payload and idempotency key shape, without reading/migrating old DFS history.
- Keep retry-safe idempotency conflict/dedup for P009; P013 may pass an idempotency key into events but does not need to dedupe yet.
- Add tests for first append, multiple append ordering, injected provider determinism, stream/root mismatch rejection, and root initialization payload.

## Acceptance Criteria

- Append creates valid ContextEvents with explicit generated fields.
- Append produces monotonic per-stream sequences.
- Append uses injected providers, not hidden `uuid` or wall clock.
- Root initialization appends `RootInitialized` with no legacy DFS migration.
- Focused tests pass together with schema/read tests.

## Verification Plan

- Run focused ContextEvent model/store tests.
- Static search the store module for hidden `uuid`, `time.`, environment reads, and legacy DFS source fallback.
- Diff review confirms no endpoint cutover or legacy double-source path is introduced in P013.

## Risks

- Append currently reads existing events to compute sequence; later integration must rely on existing Cortex per-scope locks or a stronger append lock for production concurrency.
- Full idempotent retry behavior is not complete until P009.

## Assumptions

- Workspace system append is acceptable for the Phase 1 substrate.
- P009 will close idempotency conflict/dedup behavior before write-path cutover.
