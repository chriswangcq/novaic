# Classify Gateway and Cortex Postgres Boundaries

## Problem

`gateway.db` contains auth/ops state while `cortex/operational.sqlite3` appears to be an operational projection/cache. They need explicit Postgres dispositions: migrate, defer, or retain as projection, with backup expectations and ownership notes.

This belongs under P004 because these stores are smaller than queue/Entangled but still have distinct ownership and runtime roles.

## Success Criteria

- `gateway.db` tables are classified as auth state, ops state, obsolete tables, or migration candidates.
- `cortex/operational.sqlite3` is classified as state owner or projection/cache with evidence.
- Backup expectations and eventual Postgres boundaries are documented.
- The central SQLite classification note is updated if disposition changes.
- No production cutover is attempted by this problem.
