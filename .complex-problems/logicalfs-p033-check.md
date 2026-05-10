# Check: P033 Guardrail Tightening

## Result IDs

- R031

## Verdict

success

## Criteria Map

- `No allowlist entry for novaic_cortex/workspace_files.py.` Met.
- `No transitional BlobCortexStore policy snippets.` Met for allowed snippets. `BlobCortexStore` remains only as a forbidden pattern.
- `Cortex runtime source remains blocked from /v1/objects direct access.` Met by the guardrail scan; `/v1/objects` is allowed only for `novaic-logicalfs/logicalfs/blob_store.py`.
- `Guardrail tests pass.` Met: `4 passed`.

## Execution Map

- Updated the policy module.
- Expanded scan roots to include LogicalFS.
- Ran guardrail tests and residue scan.

## Stress Test

The policy test scans Cortex, LogicalFS, and sandbox-service Python source. This catches accidental direct object API usage outside the approved LogicalFS Blob adapter.

## Residual Risk

The forbidden pattern intentionally contains the old name `BlobCortexStore`; final residue scans should classify that occurrence as guardrail-only, not stale live code.
