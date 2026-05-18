# Classify 2-4-hit low-density tests

## Problem Definition

P545 owns the 17 low-density test files with 2-4 static-residue hits each. It must classify each file without losing one-off stale expectations in a broad remainder bucket.

## Proposed Solution

Filter P531 test hits to the P545 file list, count and inspect context, then write a 17-row classification table with purpose, rationale, and follow-up status.

## Acceptance Criteria

- The P545 bucket is counted as 43 hits across 17 files.
- Every listed file has a rationale.
- Any stale or misleading test residue becomes follow-up-worthy.
- Artifacts are ready for P547/P543 reconciliation.

## Verification Plan

Use exact file-list filtering, count reconciliation, context slices, and a skeptical classification pass that distinguishes intentional regression assertions from stale behavior.

## Risks

- Low-density files are easy to under-review because each has few hits.
- Some source-level guard tests may intentionally mention retired names; classification must inspect assertion direction.

## Assumptions

- P545 owns only files with 2-4 hits after subtracting P541 and P542.
