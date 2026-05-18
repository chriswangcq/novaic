# Audit LogicalFS Sandbox Blob Fallback Residue

## Problem Definition

P553 must find and classify stale fallback, compatibility, direct materialization, and blob-as-real-time-filesystem paths that could bypass the intended Cortex -> LogicalFS -> sandboxd -> Blob Service layering.

## Proposed Solution

Split the inventory into focused residue scans by boundary:

- Cortex materialization and local shell fallback residue.
- LogicalFS / BlobObjectStore authority and object-store leakage.
- Runtime display/tool-output/base64 projection residue.
- Sandbox service / SDK compatibility or path-mount bypass residue.

Each child should record exact scan commands and classify hits as intended, risky, removable, or follow-up. The parent result should roll up the classification and decide what P554 must remediate.

## Acceptance Criteria

- Static scan terms and outputs are recorded.
- Every relevant hit bucket is classified.
- High-confidence risky residue is explicitly passed to P554.
- Intended blob artifact/display/payload usage is separated from inappropriate RO/RW semantics.
- No broad "looks fine" conclusion is accepted without file/line evidence.

## Verification Plan

Use `rg` scans over the relevant repos, targeted line-numbered reads, and artifact files under `.complex-problems/L20260516-222011/tmp/p553/`. Parent verification should compare the classified hit buckets against P552 topology and ensure no known risky anchor is unclassified.

## Risks

- Keyword scans can produce large noisy buckets.
- Some compatibility code may be intentionally retained by tests or external interfaces.
- Blob object APIs can be valid below LogicalFS but dangerous if used above the semantic boundary.

## Assumptions

- The local checkout represents the code paths being optimized in this task.
- Cleanup itself belongs to P554; P553 is inventory and classification.
