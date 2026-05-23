# Remove server-side SQLite code residue after Postgres cutover

## Problem

Postgres is now the intended server-side persistence boundary, but the repository still contains active-looking SQLite runtime branches, startup flags, migration CLIs, admin scripts, comments, and tests. This residue makes future humans and AI likely to reintroduce queue.db, gateway.db, device.db, entangled.db, or Cortex operational.sqlite3 paths after the cutover.

Scope is server-side production and developer runtime code in this workspace. Client-local cache SQLite is out of scope unless it crosses into server persistence. Archived historical docs are lower priority unless they are referenced by current runbooks or scripts.

## Success Criteria

- Server startup paths no longer pass or document SQLite database files for migrated services.
- Queue, Gateway, Device, Entangled, and Cortex current runtime entry points no longer expose SQLite as the normal or fallback server backend after the Postgres cutover.
- Migration/admin scripts that only exist to operate old SQLite server databases are removed or moved out of executable current paths.
- Current tests and residue guards reflect the Postgres-only server shape instead of preserving SQLite compatibility as a goal.
- Any remaining SQLite references are either client-local cache, historical archive, or explicitly justified non-server test substrate with a follow-up if not removable in this pass.
