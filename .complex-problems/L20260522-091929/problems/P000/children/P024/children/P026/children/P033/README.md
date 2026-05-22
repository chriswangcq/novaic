# Implement Cortex Postgres Operational Store

## Problem

Cortex needs a Postgres-backed production operational store before production can switch away from `/opt/novaic/data/cortex/operational.sqlite3`.

## Success Criteria

- Cortex source supports a Postgres operational store for all five active operational tables.
- Postgres schema preserves primary keys, unique idempotency, indexes, and JSON/text behavior.
- Existing operational store API behavior is preserved.
- Focused Cortex tests pass locally.
- No production data, config, or runtime state is changed by this implementation-only problem.
