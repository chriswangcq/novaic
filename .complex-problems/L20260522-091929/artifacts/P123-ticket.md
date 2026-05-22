# Freeze Queue Writers And Archive Final SQLite Backup

## Problem Definition

Production Queue is still active on `/opt/novaic/data/queue.db`, and `lsof` shows Queue Service plus outbox workers holding the file. A final SQLite backup must be taken only after writers/workers are frozen or stopped, with checksums and metadata recorded for rollback.

## Proposed Solution

Split this work into a command-preparation gate and an execution gate. First create a freeze/backup runbook from the P122 process inventory, including exact stop order, backup path, checksum commands, and rollback notes. Then execute the freeze and final backup in a bounded window, verifying that no Queue writer holds or mutates the SQLite file before proceeding to migration.

## Acceptance Criteria

- Freeze/backup runbook lists exact target PIDs/services and stop order.
- Queue writers/workers are stopped or frozen before final backup.
- `/opt/novaic/data/queue.db` is copied to a timestamped archive.
- Backup checksum, size, mode, owner, and mtime are recorded.
- Post-backup holder check is recorded.
- Queue writer restart remains blocked until migration or rollback decision.

## Verification Plan

Before backup, run process and `lsof` checks from P122 again. Stop/freeze the listed Queue writers in a documented order. Copy the SQLite file to an archive directory, compute checksum, stat both source and backup, and run `lsof` again. If any writer remains, record a blocker and do not migrate.

## Risks

- This creates a brief production Queue write freeze.
- Stopping workers without stopping Queue Service first may allow new claims or outbox writes.
- Restarting writers prematurely could invalidate the backup before migration.

## Assumptions

- The operator accepts a brief Queue writer freeze for the execution child.
- The active SQLite path remains `/opt/novaic/data/queue.db`.
- Rollback uses the final backup plus config/service restart back to sqlite mode until Postgres migration is verified.
