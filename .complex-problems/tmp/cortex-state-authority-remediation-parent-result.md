# Cortex State Authority Remediation Plan Summary

## Summary

The complete remediation direction is:

Use a typed state model rather than a single-storage dogma.

- SQLite becomes the durable operational state ledger/projection store for Cortex control state.
- LogicalFS/Workspace remains file/document/workspace authority.
- Redis remains lease/coordination only, guarded by SQLite fencing/generation.
- Blob remains raw-byte/artifact authority with semantic manifests outside Blob.
- Process memory is cache/config/client wiring only.

## Done

- P001/R000 defined state authority taxonomy.
- P002/R001 designed SQLite-backed active stack/status projection.
- P003/R002 replaced local NDJSON transition log with SQLite lifecycle events plus optional exporter.
- P004/R003 defined Blob payload manifest authority contract.
- P005/R004 defined live LogicalFS direction with no explicit commit and per-operation durability.
- P006/R005 defined allowed process cache/config and residue cleanup.

## Verification

- Every audited imperfect area has a matching child result.
- Every child result has a success check.
- The plan respects the user's allowance for SQLite and Redis while preventing hidden in-process authority.

## Known Gaps

- Implementation is intentionally not performed in this pass.
- Follow-up implementation should be split into phases:
  1. Add SQLite operational ledger substrate.
  2. Move active stack/status and scope transitions to SQLite.
  3. Add payload manifest and Blob lifecycle enforcement.
  4. Introduce live LogicalFS service semantics.
  5. Remove old projection walking, local NDJSON, stale docs, and compatibility fallback.

## Artifacts

- `.complex-problems/L20260510-192637`
- `.complex-problems/tmp/p001-state-taxonomy-result.md`
- `.complex-problems/tmp/p002-active-stack-result.md`
- `.complex-problems/tmp/p003-scope-log-result.md`
- `.complex-problems/tmp/p004-blob-payload-result.md`
- `.complex-problems/tmp/p005-logicalfs-result.md`
- `.complex-problems/tmp/p006-cache-docs-result.md`

