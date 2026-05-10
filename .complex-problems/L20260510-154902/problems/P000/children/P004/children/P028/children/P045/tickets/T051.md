# Static audit remaining legacy filesystem writes

## Problem Definition

Phase 3.6 has demoted active API writes to projection methods, removed runtime lifecycle bypasses, and added authority tests. Before closing Phase 3.6, remaining filesystem writes to legacy projection files must be enumerated and classified so no source-of-truth write is hiding behind old names.

## Proposed Solution

- Run static scans for write methods and literal legacy file names:
  - `context.jsonl`
  - `steps/*.json`
  - `steps/_index.jsonl`
  - `summary.md`
  - lifecycle `meta.json`
- Classify remaining production writes into:
  - projection materialization,
  - support/debug/test setup,
  - read-path compatibility,
  - suspicious residue needing follow-up.
- Confirm active API calls use projection-named methods after ContextEvent append.
- Run full Cortex suite.

## Acceptance Criteria

- Audit result lists remaining legacy write categories.
- Every remaining write has a classification or follow-up.
- No suspicious unclassified production source-of-truth write remains.
- Full Cortex suite passes.

## Verification Plan

- Static scans over `novaic_cortex` and `tests`.
- Review `api.py` call sites for projection naming.
- Run full Cortex suite.

## Risks

- Many tests intentionally construct legacy projection files; those must be classified as setup/support, not confused with active runtime writes.

## Assumptions

- Legacy projection methods may still exist until read-path cutover deletes them.
