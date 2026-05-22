# Strengthen Session Locking With Behavioral Postgres Race Tests

## Problem

The session state lock implementation has SQL/render and source-order coverage, but `P093` still needs behavioral Postgres-path evidence for the failure modes it is meant to prevent: first-dispatch missing-row races, attach revalidation after active state changes, finalize restart/no-input-loss behavior, and explicit state locking before input consumption.

## Success Criteria

- Add focused Postgres-mode behavioral tests, using either a live test database or a deterministic Postgres spy/fake, that execute session repository paths rather than only inspecting source text.
- Cover first dispatch for a missing `tq_session_state` row and verify the state row is ensured/locked before active-state decisions while input remains durable.
- Cover attach revalidation when active session identity changes between initial dispatch and after-transaction attach recording; verify the input is buffered and not consumed as an attach.
- Cover finalize with pending input and verify the locked path queues restart while preserving no-input-loss semantics.
- Keep SQLite-specific behavior isolated to existing adapter/legacy tests; do not add a broad SQLite fallback branch.
- Run the new tests with existing session and queue Postgres boundary regressions.
