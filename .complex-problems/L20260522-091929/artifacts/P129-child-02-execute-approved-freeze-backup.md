# Execute Approved Queue Freeze And Backup

## Problem

After approval, run the prepared freeze/backup runbook, create the final SQLite backup, and prove the backup is valid and no Queue writer still holds the active SQLite file.

## Success Criteria

- Refreshed pre-freeze process and holder inventory is saved.
- Approved Queue writer/worker processes are stopped or frozen.
- Timestamped backup of `/opt/novaic/data/queue.db` is created with checksum/stat/integrity artifacts.
- Post-backup `lsof` and process checks are saved.
- Migration is blocked if backup validation fails or holders remain.
