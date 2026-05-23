# Remove Queue Service SQLite runtime fallback

## Problem

Queue Service still exposes SQLite backend choices, queue.db path construction, migration CLIs, and tests that preserve SQLite compatibility as current behavior. This directly conflicts with the Postgres-only server persistence target.

## Success Criteria

- Queue Service runtime entry points use Postgres as the only server backend and no longer offer a SQLite backend selector.
- Queue worker database assembly no longer constructs or logs queue.db paths.
- Old Queue SQLite-to-Postgres migration CLIs/modules/tests are removed from current executable paths.
- Focused Queue tests and residue scans pass for the Postgres-only boundary.
