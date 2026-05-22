# Execute Queue Freeze And Final SQLite Backup

## Problem

The production Queue writers must be frozen and the active SQLite queue file backed up with checksum evidence before migration. This is the actual downtime gate and must follow the prepared runbook.

## Success Criteria

- Queue writers/workers listed in the runbook are stopped or frozen.
- A timestamped backup of `/opt/novaic/data/queue.db` is created.
- Backup checksum and file metadata are recorded.
- `lsof /opt/novaic/data/queue.db` after freeze/backup shows no active Queue writer holders, or any remaining holder is explained and blocks migration.
- Queue writer restart remains blocked until migration or rollback decision is recorded.
