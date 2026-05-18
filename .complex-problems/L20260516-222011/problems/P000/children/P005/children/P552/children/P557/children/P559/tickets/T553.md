# Map Cortex Boundary Call Paths

## Problem Definition

P559 must map how `novaic-cortex` references LogicalFS, sandbox, blob, RO/RW, materialization, and artifact concepts, and identify suspicious direct paths for later residue classification.

## Proposed Solution

Run targeted `rg` scans in `novaic-cortex`, read high-signal boundary files, and produce a call-path map artifact that classifies current Cortex boundary direction without changing code.

## Acceptance Criteria

- Scan artifacts exist for relevant Cortex boundary terms.
- High-signal files are cited.
- Current call direction is summarized.
- Suspicious direct paths are flagged for P553.

## Verification Plan

Use `rg` and bounded `sed` reads. Check that result cites file paths and does not make cleanup claims.

## Risks

- Dynamic service URLs/env names may not be captured by lexical scans.
- This is Cortex-only and does not cover sandbox internals.

## Assumptions

- P560 and P561 cover sandbox/logicalfs/blob and artifact usage separately.
