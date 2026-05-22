# Execute Queue Production Postgres Cutover And Cleanup

## Problem

After Queue Postgres implementation, migration tooling, and staging validation pass, production Queue must be cut over from `/opt/novaic/data/queue.db` to `novaic_queue` in a controlled window. All queue writers/workers must be stopped or frozen, SQLite backed up, data migrated and verified, Queue service/workers restarted in Postgres mode, smokes passed, and old SQLite residue archived as rollback-only.

## Success Criteria

- All production queue writers/workers using `/opt/novaic/data/queue.db` are identified and stopped/frozen before final backup.
- Final SQLite backup is archived with checksums.
- Migration into `novaic_queue` passes row-count and semantic invariant checks.
- Queue service and worker/outbox processes restart in Postgres mode.
- Health/API/worker/outbox smokes pass.
- No process holds `/opt/novaic/data/queue.db` after cutover.
- Old `queue.db` is archived/rollback-only and central SQLite classification/rollback notes are updated.
