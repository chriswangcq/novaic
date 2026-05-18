# Ticket: Verify archive projection cleanup

## Goal

Audit workspace archive projection/readback helpers and verify they remain archive/debug-only without reintroducing live context or raw payload leakage.

## Acceptance Criteria

- Archive projection helper behavior is inspected and classified.
- Runtime context/status paths do not depend on archive projection DFS.
- Tests or guards cover archive projection and no-DFS read behavior.
- Any stale/debug-only live leak is removed or split.
