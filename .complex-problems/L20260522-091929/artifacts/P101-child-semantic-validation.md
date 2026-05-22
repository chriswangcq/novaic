# Add Queue Migration Semantic Aggregate Validation

## Problem

The migration report needs to prove more than raw row counts. It must compare Queue-specific semantic aggregates between SQLite source and Postgres target so a copied database cannot silently lose task/saga/session states, outbox statuses, idempotency statuses, worker leases, event/outbox high-water marks, or schema version.

## Success Criteria

- Computes and compares row counts for every active migration table.
- Computes task, saga, and session state histograms.
- Computes outbox status counts for task, saga, worker lease, and session outbox tables.
- Computes idempotency status counts and worker lease state counts.
- Computes max ID/high-water values for event and outbox tables.
- Computes config schema version.
- Produces structured validation errors and a report status of `validated` or `error`.
- Tests cover validation success and at least one semantic mismatch failure.
