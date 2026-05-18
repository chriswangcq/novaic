# Run Fresh Static Residue Scan

## Problem Definition

P548 must produce current static residue scan artifacts so P533 can audit the live repository after P540 changed saga code.

## Proposed Solution

Use `rg` with the P531 residue pattern across `novaic-agent-runtime`, split matches into raw, production, and test outputs, and write count summaries under the P548/P533 temp package.

## Acceptance Criteria

- Raw scan output file exists.
- Production-only scan output file exists.
- Test-only scan output file exists.
- Count file records hit and file totals for all three buckets.
- The result calls out whether counts changed from P531.

## Verification Plan

Inspect generated artifacts with `wc`, `cut`, `sort -u`, and count commands. Compare totals against P531: raw 395 hits / 83 files, production 150 hits / 27 files, tests 245 hits / 56 files.

## Risks

- `rg` output is line-based, so multiple pattern terms on one line count as one hit line.
- Grep scans can detect stale terms but not semantic reachability.

## Assumptions

- The P531 pattern remains the intended audit pattern.
- P540 cleanup should reduce production hits if it removed optional saga API lines.
