# Archive Entangled SQLite Residue And Update Cutover Notes

## Problem

Only after production Postgres runtime and smokes succeed, old active SQLite files should be moved out of the active path and operational notes updated. This belongs under `P042` because leaving active SQLite residue after a successful cutover keeps future ambiguity alive.

## Success Criteria

- `/opt/novaic/data/entangled.db*` files are moved to a timestamped rollback/residue archive after verification succeeds.
- No running process holds the old SQLite files after archival.
- Rollback note records archive path, Postgres runtime facts, and restore steps.
- Central SQLite classification note is updated to mark Entangled SQLite as archived/rollback-only.
- Final report records what was moved, what remains, and why.
