# Execute Queue Freeze And Final SQLite Backup

## Problem Definition

The production Queue SQLite file is active and has live holders. To proceed toward Postgres migration, Queue writers/workers must be frozen in a controlled window and `/opt/novaic/data/queue.db` must be archived with checksum and integrity evidence. This step creates production Queue write downtime.

## Proposed Solution

Execute the prepared runbook only after operator confirmation of the freeze window. Refresh process and holder inventory, stop/freeze Queue ingress, workers, outbox workers, scheduler/health, and Queue Service in order, copy the SQLite file to a timestamped backup directory, compute checksums and integrity output, and record post-backup process/holder state. Do not proceed to migration if any holder remains or backup validation fails.

## Acceptance Criteria

- Operator freeze-window confirmation is recorded.
- Refreshed pre-freeze process and `lsof` evidence is saved.
- Queue writer/worker processes are stopped or frozen according to the runbook.
- Timestamped backup of `/opt/novaic/data/queue.db` is created.
- Backup checksum, stat metadata, and sqlite integrity check are recorded.
- Post-backup holder/process checks are recorded.
- Migration is explicitly allowed or blocked based on backup and holder evidence.

## Verification Plan

Compare refreshed process inventory to P122/P128, run stop commands, verify holders, copy and checksum the file, run sqlite integrity check on the backup, and store a redacted execution report under ledger artifacts.

## Risks

- Queue-dependent user workflows may fail during the freeze.
- If an external supervisor restarts Queue Service in sqlite mode, the backup can become stale and migration must be blocked.
- Force-killing a stuck process may need careful review to avoid corrupting the file.

## Assumptions

- Freeze execution must wait for explicit operator approval in this thread.
- The next migration ticket will keep Queue writers stopped until Postgres mode is verified or rollback is chosen.
