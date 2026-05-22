# Close Device DB Live-Empty Residue

## Problem

`device.db` is empty but still initialized by Device service startup, and its `ssh_keys` schema does not match code paths that query `user_id`. It should not remain as misleading empty state indefinitely.

This belongs under P004 because it is a residue/code cleanup issue, not a Postgres table-copy migration.

## Success Criteria

- Device service code paths that use `device.db` are identified and tested.
- A decision is made: keep with fixed schema and explicit ownership, migrate state elsewhere, or remove startup initialization.
- If removed, restart behavior proves `device.db` is not recreated and Device health remains good.
- If retained, schema/code are made consistent and the file is documented as current auxiliary state rather than residue.
- Rollback or restoration steps are recorded.
