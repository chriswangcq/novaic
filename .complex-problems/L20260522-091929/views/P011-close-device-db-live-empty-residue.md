# P011: Close Device DB Live-Empty Residue

Status: done
Parent: P004
Root: P000
Source Ticket: T007 (split)
Source Check: none
Package: problems/P000/children/P004/children/P011
Body: problems/P000/children/P004/children/P011/README.md
Ticket(s): T023

## Problem
`device.db` is empty but still initialized by Device service startup, and its `ssh_keys` schema does not match code paths that query `user_id`. It should not remain as misleading empty state indefinitely.

This belongs under P004 because it is a residue/code cleanup issue, not a Postgres table-copy migration.

## Success Criteria
- Device service code paths that use `device.db` are identified and tested.
- A decision is made: keep with fixed schema and explicit ownership, migrate state elsewhere, or remove startup initialization.
- If removed, restart behavior proves `device.db` is not recreated and Device health remains good.
- If retained, schema/code are made consistent and the file is documented as current auxiliary state rather than residue.
- Rollback or restoration steps are recorded.

## Subproblems
- none

## Results
- R021

## Latest Check
C021

## Bodies
- Problem: problems/P000/children/P004/children/P011/README.md
- Ticket T023: problems/P000/children/P004/children/P011/tickets/T023.md
- Result R021: problems/P000/children/P004/children/P011/results/R021.md
- Check C021: problems/P000/children/P004/children/P011/checks/C021.md

## Follow-ups
- none
