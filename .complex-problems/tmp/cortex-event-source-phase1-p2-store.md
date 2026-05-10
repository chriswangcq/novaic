# Phase 1.2: Implement append-only ContextEvent store

## Problem

Implement append/read storage for ContextEvents over the existing Cortex workspace substrate. This belongs under Phase 1 because later cutover phases need one authoritative append path before write endpoints can emit events.

## Success Criteria

- The store can initialize and read a fresh root stream without migrating old DFS history.
- Append produces a monotonic per-stream sequence and stable event id/occurred_at using injected id and clock providers.
- Read returns events in stream order and validates persisted rows.
- Append rejects stream/root mismatches and never overwrites or rewrites existing rows.
- Unit tests cover empty read, first append, multiple appends, stream isolation, explicit clock/id providers, and malformed persisted rows.
