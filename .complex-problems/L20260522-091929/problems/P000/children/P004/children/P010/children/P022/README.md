# Classify Cortex Operational SQLite State and Postgres Boundary

## Problem

Cortex currently references `/opt/novaic/data/cortex/operational.sqlite3`. It may be a durable operational state owner, a rebuildable projection/cache, or a mixed store. The live file, schema, row counts, and code ownership must be classified before deciding whether it should move to `novaic_cortex` or remain a local projection.

This belongs under P010 because Cortex operational storage has different semantics from Gateway auth/ops state.

## Success Criteria

- The live `api` host is checked for `cortex/operational.sqlite3` and any WAL/SHM files, including file metadata and open holders if present.
- Cortex process args and local code paths that reference operational SQLite are identified without recording secrets.
- Cortex schema, indexes, triggers, and row counts are captured if the DB exists.
- Each table group is classified as durable state owner, projection/cache, event log, lock/lease state, or obsolete residue.
- Future Postgres boundary and backup expectations are documented.
- No Cortex production cutover is attempted.
