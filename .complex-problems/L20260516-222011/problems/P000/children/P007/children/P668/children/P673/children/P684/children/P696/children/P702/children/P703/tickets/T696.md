# Foundational boundary residue scan

## Problem Definition

P703 must scan active docs, launch scripts, code comments, tests, and guard files for stale or misleading statements about Blob, LogicalFS, Sandboxd, Cortex, live RO/RW authority, workspace semantics, and process execution boundaries.

## Proposed Solution

Run targeted high-signal grep scans and produce a disposition artifact that classifies findings as active-cleanup, intentional-history, guard/test, acceptable-current-state, or follow-up. Do not edit production code in this ticket.

## Acceptance Criteria

- Raw scan outputs are saved.
- Disposition list is saved with evidence paths.
- Active cleanup candidates are clearly identified or explicitly absent.
- No production code/docs are modified.

## Verification Plan

- Run targeted `rg` scans over active docs/scripts/code/tests.
- Produce aggregate counts and candidate snippets.
- Manually classify high-signal candidates.
- Record result with artifacts.

## Risks

- Broad terms like ownership and workspace can create false positives.
- Guard tests intentionally contain stale terms.

## Assumptions

- Remediation is owned by P704, not this scan-only ticket.
