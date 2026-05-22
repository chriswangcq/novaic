# P129: Execute Queue Freeze And Final SQLite Backup

Status: todo
Parent: P123
Root: P000
Source Ticket: T123 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P077/children/P123/children/P129
Body: problems/P000/children/P024/children/P028/children/P077/children/P123/children/P129/README.md
Ticket(s): T125

## Problem
The production Queue writers must be frozen and the active SQLite queue file backed up with checksum evidence before migration. This is the actual downtime gate and must follow the prepared runbook.

## Success Criteria
- Queue writers/workers listed in the runbook are stopped or frozen.
- A timestamped backup of `/opt/novaic/data/queue.db` is created.
- Backup checksum and file metadata are recorded.
- `lsof /opt/novaic/data/queue.db` after freeze/backup shows no active Queue writer holders, or any remaining holder is explained and blocks migration.
- Queue writer restart remains blocked until migration or rollback decision is recorded.

## Subproblems
- P130: Confirm Queue Freeze Window Approval
- P131: Execute Approved Queue Freeze And Backup

## Results
- none

## Latest Check
none

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P077/children/P123/children/P129/README.md
- Ticket T125: problems/P000/children/P024/children/P028/children/P077/children/P123/children/P129/tickets/T125.md

## Follow-ups
- none
