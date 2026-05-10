# Implement ContextEvent store substrate

## Problem Definition

Phase 1 must establish the event-source substrate that later phases will use as Cortex context source of truth. Current Cortex context facts are still written/read through DFS-style workspace files such as `context.jsonl`, `steps/_index.jsonl`, `steps/*.json`, `summary.md`, and `meta.json`. Before cutting over write/read paths, the repository needs a deterministic event model and append/read store with explicit identity, ordering, idempotency, and no hidden time/id inputs.

## Proposed Solution

- Add a focused Cortex module for ContextEvent definitions and storage, rather than mixing new source semantics directly into existing DFS `ContextEngine` code.
- Define a strict event envelope matching the design document: schema version, event id, stream id, root scope id, monotonic sequence, optional idempotency key, occurred_at, actor, event type, payload, and generation/version fields if needed by substrate.
- Implement append/read APIs over the existing workspace storage layer so Phase 1 is self-contained and testable without yet replacing all API callers.
- Make clock and id generation explicit injectable dependencies in the store, so substrate unit tests can reproduce exact output.
- Enforce idempotency: same key and same semantic body returns/reuses the existing event; same key and different semantic body is rejected.
- Enforce validation for event type, stream/root identity, payload shape, sequence ordering, and append-only behavior.
- Add focused tests for event append/read, ordering, duplicate idempotency, conflicting idempotency, invalid events, explicit clock/id providers, and reset/no-compat initialization semantics.

## Acceptance Criteria

- A new ContextEvent substrate exists in `novaic-cortex` with explicit event type/schema definitions.
- Append/read behavior is deterministic under injected clock/id providers.
- Event append creates a total per-stream order and rejects malformed or conflicting events.
- Idempotency behavior is covered and does not silently create duplicate facts.
- The substrate can initialize a fresh root stream without migrating old DFS history.
- No existing write/read path is silently half-cut over in this phase; full integration remains tracked by later phases.

## Verification Plan

- Run focused unit tests for the new ContextEvent substrate.
- Run relevant existing Cortex tests that cover workspace/context basics to ensure the substrate addition does not regress current behavior.
- Inspect diff to ensure Phase 1 only adds the substrate/tests and does not introduce a permanent dual-source integration path.

## Risks

- If the store is too coupled to legacy DFS file shape, later phases will inherit dual-truth ambiguity.
- If time/id are generated internally, tests will not be fully reproducible and the substrate will violate the explicit dependency boundary.
- If idempotency is only advisory, retries can create duplicate context facts.
- If Phase 1 starts integrating callers prematurely, it can leave half-connected code paths that are harder to audit.

## Assumptions

- Existing workspace storage primitives can hold the event log for Phase 1.
- Old historical Cortex context data can be reset/deleted during later cutover, so Phase 1 does not need a migration reader.
- Workspace projection files may continue to exist temporarily, but this ticket only creates the event source substrate.
