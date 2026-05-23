# Remove SQLite from current startup and deployment entry points

## Problem

Current root startup scripts and service launch arguments still pass server SQLite database paths after the Postgres cutover, including Entangled and Cortex paths. These entry points are the highest-risk residue because they define how future deployments are copied or restarted.

## Success Criteria

- Current startup scripts launch migrated services with Postgres backend arguments or explicit Postgres DSN files.
- Current startup scripts no longer pass `entangled.db`, `operational.sqlite3`, `gateway.db`, `device.db`, `business.db`, or `queue.db` paths as server persistence.
- Existing unrelated root worktree edits are preserved.
- A focused residue scan over current startup/deployment paths confirms no server SQLite DB launch arguments remain.
