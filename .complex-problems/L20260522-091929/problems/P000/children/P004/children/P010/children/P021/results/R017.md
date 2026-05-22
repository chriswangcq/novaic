# Gateway SQLite Boundary Result

## Summary

Completed Gateway SQLite classification. Gateway has an active `/opt/novaic/data/gateway.db`, but live row counts and source ownership show it is only a current state owner for local auth users, refresh tokens, and small config. Legacy product/session/task/device tables are zero-row residue and should not be migrated to Postgres unless future code reclaims them.

## Done

- Captured Gateway runtime process, listener, and health endpoint.
- Captured active `gateway.db` metadata.
- Captured live schema and row counts.
- Mapped local code ownership for Gateway DB initialization, schema, auth entity store, auth routes, and thin-boundary tests.
- Classified tables:
  - migrate to `novaic_gateway`: `users`, `refresh_tokens`, `config`;
  - no migration: zero-row `entangled_sync_versions`, `sessions`, `session_messages`, `ssh_keys`, `vm_processes`, `pipeline_tasks`, `pc_clients`, `sqlite_sequence`.
- Documented backup expectations and future Postgres boundary.

## Verification

- Artifact exists at `.complex-problems/L20260522-091929/artifacts/gateway-sqlite-boundary.md`.
- Artifact line count: 219 lines.
- Post-inventory Gateway health returned healthy.
- Commands were read-only against production.

## Known Gaps

- P021 did not update the central SQLite classification note; that belongs to P023 after Cortex evidence is available.
- P021 did not implement or cut over Gateway Postgres migration.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/gateway-sqlite-boundary.md`
