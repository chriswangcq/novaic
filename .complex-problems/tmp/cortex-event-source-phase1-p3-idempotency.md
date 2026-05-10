# Phase 1.3: Enforce ContextEvent idempotency and reset semantics

## Problem

Implement retry-safe idempotency and no-compat reset semantics for the ContextEvent substrate. This belongs under Phase 1 because retries and old-data reset are core source-of-truth behavior, not later endpoint decoration.

## Success Criteria

- Re-appending with the same idempotency key and same canonical semantic body returns the existing event without appending a duplicate.
- Re-appending with the same idempotency key and a different canonical semantic body raises a clear conflict error.
- Append without idempotency key remains allowed only where the caller explicitly chooses non-idempotent event creation.
- Fresh root initialization records `RootInitialized` without reading/migrating legacy DFS history.
- Unit tests cover idempotent duplicate, idempotency conflict, non-idempotent append behavior, and no-compat initialization.
