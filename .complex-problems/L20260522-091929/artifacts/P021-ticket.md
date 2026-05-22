# Classify Gateway SQLite State

## Problem Definition

Gateway's SQLite footprint must be classified before any Postgres boundary decision. The live host may no longer have an active `gateway.db`, but Gateway source and prior cleanup may still reveal auth, file registry, or obsolete DB paths.

## Proposed Solution

Run a read-only Gateway classification pass.

1. Check the `api` host for active or archived Gateway SQLite files:
   - `/opt/novaic/data/gateway.db*`;
   - likely archive paths under `/opt/novaic/residue-archive`;
   - process holders if files exist.
2. Inspect Gateway process args and health without recording secrets.
3. Inspect local Gateway source for SQLite DB ownership:
   - `gateway/db/access.py`;
   - `gateway/db/schema.py`;
   - auth, file registry, entity boundary modules;
   - tests documenting retired DB paths.
4. If a live or archived DB is available, capture schema and row counts.
5. Classify Gateway tables/paths into auth state, file/entity ops state, obsolete residue, or migration candidate.
6. Write `.complex-problems/L20260522-091929/artifacts/gateway-sqlite-boundary.md`.

## Acceptance Criteria

- Live Gateway SQLite files are confirmed present or absent.
- Any archived Gateway SQLite evidence is recorded if present.
- Gateway process/runtime ownership is captured without secrets.
- Gateway local code ownership and SQLite references are mapped.
- Gateway disposition and future Postgres boundary are documented.
- No Gateway production cutover is attempted.

## Verification Plan

- Verify the artifact exists and includes file evidence, code evidence, classification, backup expectations, and future PG boundary.
- Verify Gateway health remains available after read-only inventory.
- Record the result and run a problem-level success check.

## Risks

- Gateway DB may already have been archived; absence must be treated as classification evidence, not a failure.
- Gateway may delegate active state to Entangled, so source references alone are not enough to prove live SQLite ownership.
- Process args may include sensitive values; redact if captured.

## Assumptions

- P021 is read-only and does not update central classification notes.
- Central note update belongs to P023 after Gateway and Cortex evidence are both available.
