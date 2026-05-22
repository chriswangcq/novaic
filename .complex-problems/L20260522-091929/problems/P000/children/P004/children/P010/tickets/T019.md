# Classify Gateway and Cortex Postgres Boundaries

## Problem Definition

Gateway and Cortex still have SQLite references with different risk profiles. `gateway.db` may contain auth or operational state, while `cortex/operational.sqlite3` may be a projection/cache or current operational state. Before migrating everything to Postgres, these stores need explicit disposition: migrate, defer, retain as projection, archive, or clean as residue.

## Proposed Solution

Perform a read-mostly classification pass and update the central SQLite classification note only if the disposition changes.

1. Inventory live files on the `api` host:
   - `/opt/novaic/data/gateway.db` and related WAL/SHM files if present;
   - `/opt/novaic/data/cortex/operational.sqlite3` and related WAL/SHM files if present;
   - file metadata, open holders, service process owners, and row counts.
2. Inspect schemas:
   - table DDL, indexes, triggers;
   - row counts and obvious stale/empty tables;
   - whether data is auth state, ops state, derived projection/cache, or obsolete residue.
3. Inspect local code ownership:
   - Gateway DB access/schema/auth/files/entity boundaries;
   - Cortex operational store, event store, projections, active stack/step result read models.
4. Classify:
   - `gateway.db` tables as auth state, ops state, obsolete, or migration candidate;
   - `cortex/operational.sqlite3` as state owner or projection/cache with evidence.
5. Define backup expectations and eventual Postgres boundaries.
6. Write a durable artifact `.complex-problems/L20260522-091929/artifacts/gateway-cortex-sqlite-boundaries.md`.
7. If the live classification changes the central note, update `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md` on the `api` host with a small, timestamped section; otherwise record that no update was needed.

## Acceptance Criteria

- Gateway live SQLite tables are inventoried and classified by disposition.
- Cortex live SQLite tables are inventoried and classified by disposition.
- Runtime file holders and process owners are captured.
- Local code ownership for Gateway and Cortex DB use is mapped.
- Backup expectations and future Postgres boundaries are documented.
- Central SQLite classification note is updated if needed, or the result explains why no update was needed.
- No production cutover is attempted.

## Verification Plan

- Verify any inventory commands are read-only except the optional classification-note update.
- Verify post-inventory service health remains unchanged.
- Verify the artifact contains row counts, table classifications, and code ownership.
- If the central note is updated, verify the remote file contains the new section.
- Record the result and run a problem-level success check.

## Risks

- `gateway.db` may have already been archived or replaced after earlier cleanup, so absence must be classified explicitly rather than treated as a command failure.
- Cortex operational state may be a rebuildable projection for some tables and a current state owner for others.
- Updating the central note is safe but still a production host write; keep it small and avoid touching service data.
- Command lines may contain secrets; redact sensitive arguments from artifacts.

## Assumptions

- P010 does not migrate Gateway or Cortex to Postgres.
- If a DB file is absent, classification should rely on live process args, local code, and existing cleanup artifacts.
- Postgres databases `novaic_gateway` and `novaic_cortex` already exist from P001 for future migrations.
