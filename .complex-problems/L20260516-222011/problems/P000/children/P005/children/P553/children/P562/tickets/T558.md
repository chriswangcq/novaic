# Audit Cortex Materialization And Local Fallback Residue

## Problem Definition

P562 must classify Cortex-side residue that could bypass the intended Workspace to LogicalFS to sandboxd execution chain.

## Proposed Solution

Split into focused Cortex residue scans:

- `Workspace.materialize()` and direct materialization/write APIs.
- local shell execution fallback or sandbox executor bypass.
- temporary backing path leakage, stable path compatibility, and old path adapter residue.

Each child records exact scans, line references, classification, and any remediation candidates.

## Acceptance Criteria

- Cortex scan commands and outputs are recorded.
- `Workspace.materialize()` is explicitly classified.
- Local fallback / sandbox bypass hits are explicitly classified.
- Temporary path / compatibility residue is explicitly classified.
- Remediation candidates are passed to P554 instead of being hidden.

## Verification Plan

Use targeted `rg` scans over `novaic-cortex/novaic_cortex`, bounded line-numbered reads, and artifact files under `.complex-problems/L20260516-222011/tmp/p562/`.

## Risks

- Some terms such as `materialize` may be valid in LogicalFS adapter naming and not risky.
- Some test fixtures may intentionally mention old paths.
- Removing fallback-like code without classification could break tests.

## Assumptions

- Cortex production path is the code under `novaic-cortex/novaic_cortex`.
