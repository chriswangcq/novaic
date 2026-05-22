# P001: Provision local Postgres infrastructure on api

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
The `api` host needs a durable Postgres foundation before any service can migrate away from SQLite. This must be local-only, restart-safe, backed by a persistent Docker volume, and easy to back up and restore. It must not cut over existing services yet.

## Success Criteria
- A Postgres Docker service is running on `api`, healthy, and restart-safe.
- Postgres is exposed only locally or on a private Docker network, not publicly.
- Per-service roles/databases exist for at least `novaic_llm_factory`, `novaic_entangled`, `novaic_queue`, `novaic_gateway`, and `novaic_cortex`.
- Credentials are stored in root-readable files, not world-readable compose files.
- A backup directory and documented/dry-run `pg_dump` command exist.
- Existing services remain healthy after provisioning.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R000: problems/P000/children/P001/results/R000.md
- Check C000: problems/P000/children/P001/checks/C000.md

## Follow-ups
- none
