# Repair Gateway And Cortex Final Classification Rows

## Problem Definition

The production Gateway and Cortex cutovers are already documented in later addenda and their live SQLite paths are absent, but the primary table in `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md` still marks `/opt/novaic/data/gateway.db` and `/opt/novaic/data/cortex/operational.sqlite3` as active. This makes the final state ambiguous for future operators and agents.

## Proposed Solution

Update only the Gateway and Cortex top-level rows in the central SQLite classification note so they match the completed cutovers: archived/rollback-only non-current SQLite snapshots, current source of truth in Postgres, and rollback archive paths under `/opt/novaic/residue-archive/gateway-pg-cutover-20260522T041053Z` and `/opt/novaic/residue-archive/cortex-pg-cutover-20260522T082503Z`. Then rerun a final classification audit across Queue, Entangled, Gateway, and Cortex; copy sanitized evidence locally; and scan new artifacts for credential patterns.

## Acceptance Criteria

- Gateway top-level classification row is rollback-only/non-current or archived and names Postgres `novaic_gateway`.
- Gateway top-level disposition points to `/opt/novaic/residue-archive/gateway-pg-cutover-20260522T041053Z`.
- Cortex top-level classification row is rollback-only/non-current or archived and names Postgres `novaic_cortex`.
- Cortex top-level disposition points to `/opt/novaic/residue-archive/cortex-pg-cutover-20260522T082503Z`.
- Fresh final classification audit reports no stale active rows for Queue, Entangled, Gateway, or Cortex.
- Sanitized local artifacts exist and pass credential-pattern scanning.

## Verification Plan

Replace the two stale rows, run a read-only audit over service rows and live path existence, verify required row phrases, copy sanitized snapshots/reports into ledger artifacts, and scan the new artifacts for DSNs, passwords, tokens, private-key markers, API-key patterns, and raw Postgres secret paths.

## Risks

- This is documentation-only, but incorrect wording could obscure rollback paths; use existing archive directories and cutover note names rather than inventing new locations.
- The full central note contains unrelated credential-related words; local evidence must be sanitized before it is committed.

## Assumptions

- Gateway and Cortex cutover results/checks remain valid.
- Live Gateway and Cortex SQLite paths should remain absent after the row update.
