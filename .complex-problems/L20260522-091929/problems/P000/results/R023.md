# T000 Result - NovAIC Postgres Unification and SQLite Residue Cleanup

## Summary

Completed the phased ledger work for unifying NovAIC persistent state around a shared Postgres service while preserving service ownership boundaries and cleaning stale SQLite residue. This run provisioned Postgres, migrated LLM Factory, classified all current SQLite owners, mapped the high-risk future migrations, and removed/archive-documented misleading empty residue.

## Root Child Results

- `R000` / P001: Postgres Docker service provisioned on `api`.
- `R001` / P002: SQLite state owners and stale residue classified; empty `business.db` archived.
- `R005` / P003: LLM Factory migrated from SQLite to Postgres.
- `R022` / P004: Core migration planning completed and Device DB residue closed.

## Completed Production Changes

- Postgres service is running locally on the `api` host with separate databases/users by service ownership.
- LLM Factory now runs on Postgres (`novaic_llm_factory`) and its old SQLite file is rollback-only.
- `business.db` was archived as residue.
- `device.db` was removed from the active path, archived, and Device code was cleaned so it no longer initializes local SQLite.
- The central SQLite classification note was updated with the current owner/residue map and Gateway/Cortex boundary update.

## Current Service Database Boundaries

- `novaic_llm_factory`: live on Postgres.
- `novaic_queue`: Postgres database provisioned; Queue remains on SQLite until implementation preserves FSM, saga, lease, session, outbox, idempotency, JSON/time, and locking semantics.
- `novaic_entangled`: Postgres database provisioned; Entangled remains on SQLite until implementation preserves schema registration, sync versions, row shape, and transition atomicity.
- `novaic_gateway`: Postgres database provisioned; future migration should include only `users`, `refresh_tokens`, and `config`.
- `novaic_cortex`: Postgres database provisioned; future migration should include all five Cortex operational SQLite tables.

## Verification

- P001, P002, P003, and P004 are checked successful.
- Health/readiness checks were run after production-affecting phases.
- Mutated production SQLite files were archived or retained as rollback-only evidence.
- The central classification note records active owners, rollback-only snapshots, archived residue, deleted Device DB residue, and backup expectations.

## Remaining Work

- Implement Queue Postgres adapter and cutover.
- Implement Entangled Postgres adapter and cutover.
- Implement Gateway Postgres auth/config adapter and cutover.
- Implement Cortex operational Postgres store and cutover.
- After stabilization, retire rollback-only SQLite snapshots according to the agreed retention policy.

## No-Overmigration Statement

This ledger did not force all services into a shared schema or a generic database layer. It keeps one Postgres infrastructure with separate databases/users and service-owned tables, avoiding a shared table soup while still removing SQLite where the migration is proven safe.
