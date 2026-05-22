# Define Queue Postgres Implementation and Cutover Plan

## Problem

After inventory and semantics mapping, the queue migration needs a phased implementation and cutover plan that preserves live service correctness, supports rollback, and verifies no state is lost or duplicated.

## Success Criteria

- A phased implementation plan exists for Postgres schema, repository adapter removal of SQLite fallback, data migration, dry-run verification, and runtime cutover.
- Pre-cutover and post-cutover checks are defined for row counts, state projections, outboxes, leases, idempotency, and health endpoints.
- Rollback boundaries are documented.
- No production queue cutover is attempted.
