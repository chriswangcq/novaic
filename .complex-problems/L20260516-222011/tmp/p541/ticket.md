# Classify lifecycle and recovery test hits

## Problem Definition

P541 owns the high-density test hits in finalize/recovery/session-lifecycle files. These tests intentionally mention terms such as `remaining_stack`, `suspected_dead`, `wake_finalize`, `active`, and recovery/outbox vocabulary, but the review must verify whether each use is current regression coverage or stale residue.

## Proposed Solution

Filter P531 test hits to the seven P541 files, count hits by file, inspect context snippets, and write a classification table with purpose/rationale/follow-up status for each file.

## Acceptance Criteria

- All P541-owned files are filtered and counted.
- Each file has a purpose/category rationale.
- Any stale or misleading lifecycle/recovery test residue is identified as follow-up-worthy.
- Counts are recorded for P544 reconciliation.

## Verification Plan

Compare the filtered file count and hit count to the known P541 file list, inspect source context around hits, and run a targeted classification check that distinguishes intentional regression vocabulary from dead expectations.

## Risks

- These tests deliberately mention old failure modes, so a naive keyword scan can over-report harmless residue.
- Conversely, tests that assert stale compatibility behavior should be surfaced rather than preserved.

## Assumptions

- P541 should classify only the seven files named in the split child problem.
