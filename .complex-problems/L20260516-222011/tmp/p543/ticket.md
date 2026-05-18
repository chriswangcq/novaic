# Split low-density boundary test classification

## Problem Definition

P543 owns all test hit files not assigned to P541 or P542. This remainder has many files with few hits each, so the risk is losing one-off stale tests in a vague "misc" bucket.

## Proposed Solution

Split the low-density remainder into files with 2-4 hits, files with exactly 1 hit, and a reconciliation child. Each child will classify every owned file with a rationale and surface stale or misleading tests.

## Acceptance Criteria

- Every remaining low-density test file is assigned exactly once.
- Files with 2-4 hits and files with 1 hit are separately classified.
- Stale or misleading one-off tests become follow-up-worthy.
- Low-density counts reconcile back to P535/P531.

## Verification Plan

Derive the remainder set by subtracting P541 and P542 file lists from P531 test files. Count files/hits by bucket, classify each bucket, then reconcile the low-density totals.

## Risks

- "Misc" classification can hide stale tests, so child grouping must be exact and count-driven.
- Single-hit files can still be important guardrails; do not delete or dismiss them without context.

## Assumptions

- P541 and P542 file lists are fixed ownership boundaries for high-density groups.
