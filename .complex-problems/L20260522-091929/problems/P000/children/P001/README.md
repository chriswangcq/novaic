# Provision local Postgres infrastructure on api

## Problem

The `api` host needs a durable Postgres foundation before any service can migrate away from SQLite. This must be local-only, restart-safe, backed by a persistent Docker volume, and easy to back up and restore. It must not cut over existing services yet.

## Success Criteria

- A Postgres Docker service is running on `api`, healthy, and restart-safe.
- Postgres is exposed only locally or on a private Docker network, not publicly.
- Per-service roles/databases exist for at least `novaic_llm_factory`, `novaic_entangled`, `novaic_queue`, `novaic_gateway`, and `novaic_cortex`.
- Credentials are stored in root-readable files, not world-readable compose files.
- A backup directory and documented/dry-run `pg_dump` command exist.
- Existing services remain healthy after provisioning.
