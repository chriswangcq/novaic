# CI and Lint Helper Residue Scan Ticket

## Problem Definition

CI workflows and lint/test helper scripts may contain stale compatibility/fallback/migration wording or historical policy comments.

## Proposed Solution

Scan CI and lint helper surfaces, classify hits, remove safe stale residue, and run representative helper checks.

## Acceptance Criteria

- CI/lint helper files scanned.
- Hits classified as active guard/policy, harmless text, or stale residue.
- Safe stale residue removed.
- Verification recorded.

## Verification Plan

- `rg` scans over `.github/` and `scripts/ci`.
- Run affected lint/helper scripts where feasible.
