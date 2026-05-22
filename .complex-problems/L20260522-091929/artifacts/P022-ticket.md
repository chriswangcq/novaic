# Classify Cortex Operational SQLite State

## Problem Definition

Cortex uses `/opt/novaic/data/cortex/operational.sqlite3` in production. It must be classified table by table as durable state, event log, projection/cache, lock/lease state, or obsolete residue before deciding what belongs in `novaic_cortex` Postgres.

## Proposed Solution

Run a read-only Cortex classification pass.

1. Check the `api` host for:
   - `/opt/novaic/data/cortex/operational.sqlite3*`;
   - file metadata and open holders;
   - Cortex process args without secrets;
   - Cortex health if available.
2. Capture live SQLite schema, indexes, triggers, and row counts.
3. Inspect local Cortex source:
   - `operational_store.py`;
   - context event store/projection/read model files;
   - active stack and step result projections;
   - scope locks/state/transition modules.
4. Classify table groups as durable state owner, event log, projection/cache, lock/lease, or obsolete residue.
5. Define future Postgres boundary and backup expectations.
6. Write `.complex-problems/L20260522-091929/artifacts/cortex-sqlite-boundary.md`.

## Acceptance Criteria

- Live Cortex operational SQLite files are confirmed present or absent.
- Runtime process and open file holders are captured without secrets.
- Schema, indexes, triggers, and row counts are captured if DB exists.
- Local code ownership is mapped.
- Each table group is classified by disposition.
- Future Postgres boundary and backup expectations are documented.
- No Cortex production cutover is attempted.

## Verification Plan

- Verify the artifact exists and includes runtime, schema/count, code ownership, classification, and backup sections.
- Verify Cortex health/listener remains available after read-only inventory.
- Record the result and run a problem-level success check.

## Risks

- Operational SQLite may mix durable event logs and rebuildable read models.
- Some tables may be empty now but still required by active code.
- Cortex command lines may contain sensitive auth arguments; redact them.

## Assumptions

- P022 is read-only and does not update central classification notes.
- Central note update belongs to P023 after both Gateway and Cortex classifications are done.
