# Classify Production Residue Hits Ticket

## Problem Definition

P531 found 150 production static residue hits across 27 production files. These must be classified with source-context review before P532 can close.

## Proposed Solution

Split production classification into queue service production hits, task queue production hits, and a production reconciliation step. Any risky production residue must become follow-up.

## Acceptance Criteria

- Every production file from P531 is covered by a classification artifact.
- Production hits are classified as live/expected, documentation/comment, or follow-up-worthy.
- Risky residue is not silently waived.
- Classified production counts reconcile with P531's 150 production hits.

## Verification Plan

- Use P531 `static-residue-production.txt` and `static-residue-production-files.txt`.
- Inspect source context by file group.
- Reconcile counts after child classifications.

## Risks

- Broad terms like `optional`, `fallback`, and `publish` can be expected in one file and risky in another.

## Assumptions

- Test hits are handled separately by P535.
