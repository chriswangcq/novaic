# Implement ContextEvent append/read store

## Problem Definition

P008 must provide the append-only storage layer for ContextEvents over the existing Cortex workspace storage substrate. The schema exists, but there is not yet a store that initializes fresh streams, assigns monotonic sequence, injects clock/id providers, appends rows, and reads/revalidates them in order.

## Proposed Solution

- Add a `ContextEventStore` module under `novaic-cortex/novaic_cortex/`.
- Store event rows at a single root-stream-owned logical path under the root scope, for example `<root_scope_path>/context_events/events.jsonl`.
- Accept explicit `clock` and `id_provider` dependencies at construction; do not read time or generate ids in the domain model.
- Implement:
  - `read_events(root_scope_path)` to read, parse, validate, and return ordered `ContextEvent` objects;
  - `append(...)` to assign `seq`, `event_id`, and `occurred_at`, validate the event, and append one JSON line;
  - `initialize_root(...)` to append `RootInitialized` for a fresh stream without reading or migrating legacy DFS history.
- Keep idempotency conflict/dedup policy minimal or absent here if needed, because P009 is dedicated to full idempotency behavior. If any idempotency hook exists in P008, it must be clearly completed in P009.
- Add tests for empty read, first append, multiple append ordering, injected clock/id providers, stream/root mismatch rejection, malformed persisted row rejection, and fresh root initialization.

## Acceptance Criteria

- Store append/read APIs exist and operate over `Workspace` system IO only.
- Appended events get monotonic per-stream sequence numbers.
- Generated fields come only from explicit injected providers.
- Read validates persisted rows and returns ordered `ContextEvent` objects.
- Fresh root initialization writes `RootInitialized` without legacy DFS migration.
- Focused tests pass.

## Verification Plan

- Run focused store tests with `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk`.
- Run existing workspace/context event model tests.
- Review static search for hidden `uuid`, direct wall-clock default in core append logic, and old DFS source fallback.

## Risks

- Naive read-all append is acceptable for substrate tests, but later production code may need lock/transaction guarantees from caller or workspace lock.
- If P008 implements partial idempotency, P009 may be confusing; keep idempotency either absent or clearly separated.

## Assumptions

- Workspace `_sys_append_line` and `read` are sufficient for Phase 1 substrate tests.
- Per-stream serialization/locking is handled by higher-level Cortex mutation locks in later integration phases.
