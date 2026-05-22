# Close Device DB Live-Empty Residue

## Problem Definition

`device.db` was previously a live-empty auxiliary SQLite file: Device startup initialized it, but its local tables were empty and durable device state lived elsewhere. The user explicitly requested that `device.db` be removed and thoroughly cleaned.

## Proposed Solution

Use the already-applied Device cleanup as the bounded execution scope, then verify and record it in the ledger.

1. Confirm the active production path `/opt/novaic/data/device.db` is absent and was archived.
2. Confirm Device service code no longer initializes local SQLite or imports the removed local DB access module.
3. Confirm Device now uses the file-backed SSH key store instead of local SQLite.
4. Confirm no active remote code reference can recreate `device.db`.
5. Confirm Device health remains good after cleanup.
6. Record rollback/restoration notes.

## Acceptance Criteria

- Active `/opt/novaic/data/device.db` is absent.
- Deleted DB archive location is recorded.
- Device startup no longer initializes `device.db`.
- Local `device/db_access.py` is removed from current Device service code.
- SSH-key behavior has a non-SQLite backing path.
- Device health check succeeds.
- The central SQLite classification note records `device.db` as deleted/archived residue.

## Verification Plan

- Run remote `test ! -e /opt/novaic/data/device.db`.
- Search remote Device service code for `device.db`, `db_access`, and `init_database`.
- Check the central classification note for the deleted/archived `device.db` row.
- Run Device health check.
- Record any remaining references as follow-up if they can recreate the DB.

## Risks

- Stale imports or startup code could recreate the SQLite file on next restart.
- SSH key endpoints could fail if the replacement backing store is incomplete.
- Archive deletion would remove rollback evidence; keep archive until the agreed retention window expires.

## Assumptions

- The prior code cleanup and restart were intentional user-approved work.
- P011 should ledger and verify the current state, not re-run destructive cleanup.
