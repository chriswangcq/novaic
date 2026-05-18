# Repository Scripts Residue Scan Ticket

## Problem Definition

Top-level and package-level scripts may contain stale compatibility/fallback/migration wording or old policy comments.

## Proposed Solution

Scan script files, classify hits, remove safe stale residue, and run representative verification.

## Acceptance Criteria

- Script files scanned.
- Hits classified.
- Safe stale residue removed.
- Verification recorded.

## Verification Plan

- `rg` scans over `scripts/` and executable shell/python helper files.
- Run affected script checks where applicable.
