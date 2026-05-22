# Unify NovAIC persistent state on Postgres and remove stale database residue

## Problem

The production `api` host currently has service state spread across several SQLite files under `/opt/novaic/data` and `/opt/novaic/llm-factory/data`: `queue.db`, `entangled.db`, `llm_factory.db`, `gateway.db`, `device.db`, `business.db`, and `cortex/operational.sqlite3`. The desired direction is a unified Postgres infrastructure while preserving service ownership boundaries and cleaning old residue such as empty or obsolete SQLite files and dead code paths.

This is production state work. It must be phased, reversible, and evidence-driven. The target architecture should use one Postgres service with separate databases/users per owning service rather than a shared table soup. Old residue should be archived or removed only after verifying that it is not the current state owner.

## Success Criteria

- A Postgres Docker service is provisioned on the `api` host with persistent volume, local-only exposure, health checks, credentials stored outside world-readable files, and backup/restore commands documented or installed.
- Each current SQLite database is classified as migrate-now, migrate-later, archive, or delete, with evidence from runtime wiring, schema, row counts, and code references.
- `llm-factory` is migrated first or explicitly scheduled as the first application migration, because it is already Dockerized and has low blast radius.
- `queue.db` is not migrated until its FSM/outbox/lease semantics are mapped to Postgres transactions, JSONB, and locking primitives.
- Legacy residue such as empty `business.db` and unused/empty `device.db` paths is cleaned by archive/removal or converted into explicit documented non-current paths; no misleading active-looking empty database remains without explanation.
- The live services remain healthy after each phase, with rollback instructions and backups for every mutated production file or database.
