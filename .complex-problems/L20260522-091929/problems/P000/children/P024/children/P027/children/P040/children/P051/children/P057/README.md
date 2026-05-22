# Prepare Safe Entangled Postgres REST Staging Target

## Problem

Before REST smokes can run, there must be a safe Postgres target with migrated or fixture data that is not production traffic-facing. Prepare that target, import data using the migration command or an equivalent staging-safe path, and record a redacted setup report. This belongs under `P051` because runtime REST validation needs a concrete Postgres target.

## Success Criteria

- A safe Postgres database/target is selected or created for REST staging without touching production traffic.
- DSN handling uses a redacted secret file or non-secret test connection label.
- Migration/import runs against the staging target or a clear fixture target with no production mutations.
- Setup report records target label, migrated tables/counts, semantic checks, and cleanup state without secrets.
- Any target setup blocker is documented with exact commands/results and no raw secrets.
