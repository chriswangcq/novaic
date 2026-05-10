# State Authority Taxonomy And Storage Rules

## Problem

Cortex needs a clear rule for what state may live in LogicalFS/Workspace, SQLite, Redis, Blob, or process memory. Without this taxonomy, future work can accidentally move semantic authority into caches, locks, or artifact stores.

## Success Criteria

- Define state classes: semantic authority, event ledger, projection, coordination lease, artifact bytes, observability, process cache/config.
- Decide allowed storage engines for each class: LogicalFS/Workspace, SQLite, Redis, Blob, memory.
- Define invariants for recovery, replay, migration, and tests.
