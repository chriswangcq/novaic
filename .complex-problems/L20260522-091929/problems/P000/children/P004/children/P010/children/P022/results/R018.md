# Cortex Operational SQLite Boundary Result

## Summary

Completed Cortex operational SQLite classification. `/opt/novaic/data/cortex/operational.sqlite3` is a current durable operational state owner, not residue. All five live tables should move to `novaic_cortex` for a first Postgres cutover unless a tested rebuild path is created before migration.

## Done

- Captured Cortex runtime process, listener, and health/readiness.
- Captured active `operational.sqlite3` metadata.
- Captured live schema, indexes, and row counts.
- Mapped local code ownership for operational store, registry, active-stack projection, scope transition events, workspace writes, and API reads.
- Classified tables:
  - migrate: `scope_events`, `scope_projection`, `active_stack_projection`, `payload_manifest`;
  - recreate or migrate metadata: `cortex_operational_meta`;
  - no obsolete residue found inside the live operational DB.
- Documented future Postgres boundary and backup expectations.

## Verification

- Artifact exists at `.complex-problems/L20260522-091929/artifacts/cortex-sqlite-boundary.md`.
- Artifact line count: 175 lines.
- Post-inventory Cortex readiness returned ok with registry/blob/Redis lock checks green.
- Commands were read-only against production.

## Known Gaps

- P022 did not update the central SQLite classification note; that belongs to P023 after Gateway and Cortex evidence is combined.
- P022 did not implement or cut over Cortex Postgres migration.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/cortex-sqlite-boundary.md`
