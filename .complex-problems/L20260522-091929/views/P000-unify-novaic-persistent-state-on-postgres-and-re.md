# P000: Unify NovAIC persistent state on Postgres and remove stale database residue

Status: done
Parent: none
Root: P000
Source Ticket: none (none)
Source Check: none
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

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

## Subproblems
- P001: Provision local Postgres infrastructure on api
- P002: Classify SQLite state owners and stale residue
- P003: Migrate llm-factory from SQLite to Postgres
- P004: Plan core database migrations and close legacy residue
- P024: Implement Remaining Service Postgres Cutovers

## Results
- R023

## Latest Check
C154

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R023: problems/P000/results/R023.md
- Check C023: problems/P000/checks/C023.md
- Check C154: problems/P000/checks/C154.md

## Follow-ups
- P024: Implement Remaining Service Postgres Cutovers
