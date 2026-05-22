# P123: Freeze Queue Writers And Archive Final SQLite Backup

Status: todo
Parent: P077
Root: P000
Source Ticket: T120 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P077/children/P123
Body: problems/P000/children/P024/children/P028/children/P077/children/P123/README.md
Ticket(s): none

## Problem
The final SQLite queue backup must be taken while production queue writers and workers are frozen or stopped, otherwise migration can miss writes or produce inconsistent state.

## Success Criteria
- All identified Queue writers/workers are stopped, frozen, or otherwise prevented from writing.
- `/opt/novaic/data/queue.db` is backed up to a timestamped rollback archive.
- Backup checksum and file metadata are recorded.
- A post-backup check confirms no writer process still holds or mutates the active SQLite queue file.
- The backup location is recorded without exposing unrelated credentials.

## Subproblems
- none

## Results
- none

## Latest Check
none

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P077/children/P123/README.md

## Follow-ups
- none
