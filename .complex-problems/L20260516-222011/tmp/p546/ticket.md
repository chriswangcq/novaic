# Classify single-hit boundary tests

## Problem Definition

P546 owns 21 low-density files with exactly one static-residue hit each. Each hit must still be classified because a single stale assertion can preserve old architecture assumptions.

## Proposed Solution

Filter P531 test hits to the P546 file list, count them, inspect the exact hit lines, and write a 21-row classification table with purpose/rationale/follow-up status.

## Acceptance Criteria

- The P546 bucket is counted as 21 hits across 21 files.
- Every listed file has a rationale.
- Any stale or misleading one-off test becomes follow-up-worthy.
- Artifacts are ready for P547/P543 reconciliation.

## Verification Plan

Use exact file-list filtering and hit-line review. Stress-check for one-off tests that assert retired behavior positively instead of guarding its absence.

## Risks

- Single-hit tests can look harmless by volume but still encode stale behavior.
- Many filenames are PR-specific, so classification should rely on the actual hit line rather than title alone.

## Assumptions

- P546 owns only exactly-one-hit files after subtracting P541/P542/P545.
