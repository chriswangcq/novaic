# Add Queue Migration Semantic Aggregate Validation

## Problem Definition

Raw row counts are not enough to trust a Queue migration. The migration report must compare domain-level aggregates between source and target: state histograms, outbox status counts, idempotency statuses, worker lease states, event/outbox high-water values, and schema version.

## Proposed Solution

1. Extend `queue_service/db/migration.py` with semantic aggregate collection:
   - `count_by` helpers for state/status columns;
   - `max(id)` or equivalent high-water helpers for event/outbox tables;
   - config version extraction.
2. Add `validate_queue_migration(source_db, target_db, report=None)`:
   - refreshes/compares row counts for every migration table;
   - computes source and target aggregate maps;
   - stores both sides under `report.semantic_aggregates`;
   - sets `status="validated"` on match;
   - appends structured errors and sets `status="error"` on mismatch.
3. Keep validation DB-surface generic so fake target tests and real Postgres wrapper can share it.
4. Add tests for success and semantic mismatch failure.

## Acceptance Criteria

- Validation compares row counts for all active tables.
- Validation computes task/saga/session state histograms.
- Validation computes task/saga/worker/session outbox status counts.
- Validation computes idempotency status counts and worker lease state counts.
- Validation computes max event/outbox IDs and config schema version.
- Validation writes source/target aggregates into the report and returns `validated` or `error`.
- Tests cover success and at least one mismatch failure.

## Verification Plan

- Add/extend migration validation tests.
- Run all migration tests and compile checks.

## Risks

- Event/outbox IDs are text in current schema; high-water validation should compare deterministic max text values rather than invent integer coercion.

## Assumptions

- CLI invocation and report-file writing remain in P103.
