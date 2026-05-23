# Execute Approved Queue Freeze And Backup

## Problem Definition

Approval is recorded and the prepared runbook is ready. Production Queue writers must now be stopped/frozen and `/opt/novaic/data/queue.db` must be backed up with checksum and integrity evidence before migration.

## Proposed Solution

Run a remote freeze/backup script on `api.gradievo.com` that refreshes process and holder inventories, gracefully stops Queue ingress, workers, outbox workers, scheduler/health, and Queue Service in the runbook order, verifies holders, copies `/opt/novaic/data/queue.db` to a timestamped backup directory, writes checksum/stat/integrity artifacts, and produces a redacted JSON/Markdown report for the ledger.

## Acceptance Criteria

- Refreshed pre-freeze process and holder inventory is saved.
- Approved Queue writer/worker processes are stopped or frozen.
- Timestamped backup of `/opt/novaic/data/queue.db` is created.
- Backup checksum, stat metadata, and sqlite integrity check are recorded.
- Post-backup `lsof` and process checks are saved.
- Migration is blocked if backup validation fails or holders remain.

## Verification Plan

Inspect the freeze report, confirm backup files exist, confirm source/backup checksums match, confirm sqlite integrity is `ok`, confirm post-backup Queue holder list is empty, and confirm production Queue health on port `19997` is no longer reachable because it is intentionally frozen.

## Risks

- Production Queue write requests fail while Queue Service is frozen.
- A supervisor may restart sqlite-mode services; the script must check and report if this happens.
- If `sqlite3` is missing, integrity check may be blocked; migration should not proceed until integrity is verified.

## Assumptions

- User approval from P130 covers this execution.
- Queue writers remain stopped until migration or rollback.
