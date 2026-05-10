# Phase 1.2.2: ContextEvent append and root initialization

## Problem

Implement the write side of the ContextEvent store: append one event with generated fields from explicit providers, monotonic sequence assignment, and fresh root stream initialization. This belongs under P008 because later write-path cutover needs one durable append primitive before endpoint migration starts.

## Success Criteria

- Append assigns `seq`, `event_id`, and `occurred_at` from current stream length and injected providers.
- Append validates stream/root identity and event envelope before persisting.
- Multiple appends produce monotonic per-stream ordering.
- Fresh root initialization writes `RootInitialized` without reading or migrating old DFS history.
- Tests cover first append, multiple appends, injected provider determinism, stream/root mismatch rejection, and root initialization.
