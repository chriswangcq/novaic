# LogicalFS boundary map implementation

## Problem Definition

P700 needs an evidence-backed LogicalFS boundary map. LogicalFS should be classified as the realtime logical RO/RW file authority above Blob and below Cortex/shell orchestration, while honestly recording whether it currently exists as an independent service, a library/substrate, or both.

## Proposed Solution

Inspect `novaic-logicalfs`, Cortex LogicalFS integration, docs, launch scripts, and P695 evidence. Produce a boundary map that records module/entrypoint evidence, role, backing dependencies, consumers, deployment status, and stale claims. Patch only safe misleading docs/guard residue if clearly wrong.

## Acceptance Criteria

- LogicalFS module/entrypoint/service evidence is listed with stable paths.
- LogicalFS role is clearly separated from Blob byte storage and Cortex semantic state.
- Current deployment shape is stated honestly: independent service vs library/substrate vs embedded use.
- Cortex usages are classified as client/facade/orchestration unless evidence proves ownership.
- Misleading LogicalFS boundary claims are patched or explicitly recorded.
- Focused checks pass if files change.

## Verification Plan

- Inspect `novaic-logicalfs`, `novaic-cortex/novaic_cortex/logical_fs.py`, `workspace_authority.py`, relevant docs, and launch references.
- Run targeted scans for LogicalFS service/authority/boundary wording.
- Save boundary map and verification artifacts.
- Run LogicalFS tests or syntax checks as appropriate.

## Risks

- LogicalFS may be a package/substrate today while the desired architecture discusses a service; overclaiming either way would mislead future work.
- Cortex shell integration legitimately constructs LogicalFS views; this is not necessarily ownership violation.

## Assumptions

- Honest current-state classification is preferred over pretending final architecture is fully implemented.
