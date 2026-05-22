# Freeze Queue Writers And Archive Final SQLite Backup

## Problem

The final SQLite queue backup must be taken while production queue writers and workers are frozen or stopped, otherwise migration can miss writes or produce inconsistent state.

## Success Criteria

- All identified Queue writers/workers are stopped, frozen, or otherwise prevented from writing.
- `/opt/novaic/data/queue.db` is backed up to a timestamped rollback archive.
- Backup checksum and file metadata are recorded.
- A post-backup check confirms no writer process still holds or mutates the active SQLite queue file.
- The backup location is recorded without exposing unrelated credentials.
