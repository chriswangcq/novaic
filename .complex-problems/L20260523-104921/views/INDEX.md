# Complex Problem Ledger

Ledger: L20260523-104921
Schema: v6
Root: P000 - Remove server-side SQLite code residue after Postgres cutover
Status: done
Updated: 2026-05-23T04:11:45+00:00

## Problem Tree
- [done] P000: Remove server-side SQLite code residue after Postgres cutover
  - [done] P001: Remove SQLite from current startup and deployment entry points
  - [done] P002: Remove Queue Service SQLite runtime fallback
  - [done] P003: Remove Gateway and Device server SQLite utilities
  - [done] P004: Remove Cortex and Entangled server SQLite fallback paths
  - [done] P005: Update residue guards, tests, and ledger evidence

## Active

## Blocked

## Done
- [x] P000: Remove server-side SQLite code residue after Postgres cutover
- [x] P001: Remove SQLite from current startup and deployment entry points
- [x] P002: Remove Queue Service SQLite runtime fallback
- [x] P003: Remove Gateway and Device server SQLite utilities
- [x] P004: Remove Cortex and Entangled server SQLite fallback paths
- [x] P005: Update residue guards, tests, and ledger evidence

## Tickets
- [done] T000: Delete migrated server SQLite code paths -> P000 (split)
- [done] T001: Make current startup Postgres-only -> P001 (one_go)
- [done] T002: Make Queue Service Postgres-only at runtime -> P002 (one_go)
- [done] T003: Remove Gateway and Device SQLite current-path utilities -> P003 (one_go)
- [done] T004: Remove Cortex and Entangled SQLite server runtime fallbacks -> P004 (one_go)
- [done] T005: Guard service-side SQLite residue -> P005 (one_go)

## Latest Checks
- [success] C000: P001 Success. The current startup/deployment entry point for backend processes no longer launches migrated server services with SQLite database files, and the necessary Cortex parser change lets the startup script omit the old operational SQLite path in Postgres mode.
- [success] C001: P002 Success for the Queue runtime-fallback problem. `R001` removes the active server runtime selector, queue.db construction, migration CLIs, SQLite busy compatibility boundary, and updates outbox-worker DB assembly to explicit Postgres DSN inputs.
- [success] C002: P003 Success. `R002` removes active Gateway/Device server SQLite utilities and makes Gateway auth/config runtime Postgres-only.
- [success] C003: P004 P004 success: Cortex and Entangled server SQLite fallback paths are gone from current service code.
- [success] C004: P005 P005 success: SQLite residue guard is CI-runnable, passes locally, and active service paths scan clean.
- [success] C005: P000 P000 success: server-side SQLite residue is removed from current runtime paths and guarded.
