# Execute Queue Production Postgres Cutover Safely

## Problem Definition

Queue Postgres implementation and staging validation are complete, but production still needs a controlled cutover from the legacy SQLite queue file to the production Postgres database. This is a high-risk operational change because active writers/workers can mutate `/opt/novaic/data/queue.db`, data must be migrated with invariants checked, services must restart in Postgres mode, and the old SQLite file must become rollback-only residue rather than an active path.

## Proposed Solution

Split the production cutover into explicit child problems: preflight and source-control readiness, production inventory/freeze, final SQLite backup with checksums, migration and invariant verification, Postgres-mode restart for Queue Service and workers, production smokes, and rollback-only cleanup/documentation. Do not execute destructive cleanup or production restarts until preflight proves the target, processes, backup path, and rollback plan.

## Acceptance Criteria

- Production queue writers/workers touching `/opt/novaic/data/queue.db` are identified and frozen/stopped before backup.
- Final SQLite backup and checksum artifacts are created.
- Migration into `novaic_queue` completes with row-count and semantic invariant checks.
- Queue Service and worker/outbox processes restart in Postgres mode.
- Health, API, worker, and outbox smokes pass after cutover.
- No process holds `/opt/novaic/data/queue.db` after cutover.
- Old SQLite file is archived as rollback-only and central SQLite cleanup notes are updated.

## Verification Plan

Use child checks for each operational gate. Require explicit command output artifacts for process inventory, backup checksums, migration report, service health/readiness, smoke results, `lsof` checks, and cleanup notes. Treat missing production credentials, unknown process owners, failing invariant checks, or uncommitted cutover code as blockers rather than proceeding.

## Risks

- Production writers may mutate SQLite during backup if freeze is incomplete.
- A migration may pass row counts but fail semantic invariants such as lifecycle state projections or idempotency replay behavior.
- Restarting Queue workers in Postgres mode before the service is healthy can create partial failure loops.
- Cleanup can erase rollback capability if performed before the Postgres runtime is verified.

## Assumptions

- The production target database is `novaic_queue`, but credentials and credential-file paths must remain redacted in artifacts.
- Production cutover should only use committed/pushed code, not an ad hoc dirty staging checkout.
- Rollback remains file-restore plus config revert until the old SQLite file is explicitly retired after verification.
