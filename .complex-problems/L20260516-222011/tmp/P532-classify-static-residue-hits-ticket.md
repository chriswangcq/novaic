# Classify Static Residue Hits Ticket

## Problem Definition

The P531 scan produced 395 raw hits, including 150 production hits and 245 test hits. P512 requires every remaining hit to be classified, with no unclassified risky legacy path left behind.

## Proposed Solution

Split classification into production hit classification, test hit classification, and final risk/unclassified reconciliation. Production hits must receive source-context review; test hits may be grouped by regression/boundary intent.

## Acceptance Criteria

- Every raw hit is classified directly or through an explicit grouped rationale.
- Production hits are separated from test hits.
- Any risky production residue becomes a follow-up problem.
- No unclassified hit remains.

## Verification Plan

- Use P531 raw/production/test split artifacts.
- Produce classification artifacts under `.complex-problems/L20260516-222011/tmp/`.
- Check classified counts against P531 counts.

## Risks

- Broad terms such as `optional`, `fallback`, and `remaining_stack` can be expected vocabulary or real residue depending on context.
- Grouping too broadly can hide risky paths.

## Assumptions

- P531 scan output is authoritative.
