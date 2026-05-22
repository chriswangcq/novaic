# Archive Old Queue SQLite Residue And Update Cleanup Notes

## Problem

After production Postgres mode passes smokes, the old SQLite queue file must stop looking like an active runtime path. It should remain available only for rollback until retirement, and central cleanup notes must reflect the new source of truth.

## Success Criteria

- `/opt/novaic/data/queue.db` is moved, renamed, permissioned, or otherwise marked rollback-only according to the rollback plan.
- No production process holds the old SQLite file after cleanup.
- Central SQLite classification and rollback notes are updated to say Queue runtime source of truth is Postgres.
- Cleanup preserves the final backup and checksum.
- The report states whether the rollback-only SQLite artifact can be retired later or must be retained for a defined window.
