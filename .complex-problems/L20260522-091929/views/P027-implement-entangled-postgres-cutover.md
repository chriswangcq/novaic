# P027: Implement Entangled Postgres Cutover

Status: done
Parent: P024
Root: P000
Source Ticket: T024 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027
Body: problems/P000/children/P024/children/P027/README.md
Ticket(s): T036

## Problem
Entangled still owns active entity, sync, chat, device, model, execution, and user state in `/opt/novaic/data/entangled.db`. It should be migrated to the existing `novaic_entangled` Postgres database while preserving schema registration, sync-version monotonicity, row shapes, and transition atomicity.

## Success Criteria
- Entangled has a Postgres-backed production store for all active tables identified in P009.
- Schema registration and `entangled_sync_versions` behavior are preserved.
- Entity row shapes, JSON behavior, API responses, and sync/client expectations remain compatible.
- Existing Entangled SQLite state is backed up and migrated with row-count, max-version, and representative API checks.
- Entangled runtime config is switched to Postgres and health/readiness/WebSocket smoke checks pass.
- The old SQLite file is retained only as rollback evidence and documented in the central classification note.

## Subproblems
- P038: Implement Entangled Postgres adapter and runtime boundary
- P039: Port Entangled schema registration and entity store semantics to Postgres
- P040: Build Entangled migration tooling and staging validation
- P041: Entangled production Postgres cutover preflight
- P042: Execute Entangled production Postgres cutover

## Results
- R070

## Latest Check
C074

## Bodies
- Problem: problems/P000/children/P024/children/P027/README.md
- Ticket T036: problems/P000/children/P024/children/P027/tickets/T036.md
- Result R070: problems/P000/children/P024/children/P027/results/R070.md
- Check C074: problems/P000/children/P024/children/P027/checks/C074.md

## Follow-ups
- none
