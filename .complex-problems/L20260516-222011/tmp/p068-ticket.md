# Active Docs Migration and Legacy Residue Scan Ticket

## Problem Definition

Active documentation may still describe migration, fallback, compatibility, or old paths as current guidance after the final architecture moved on.

## Proposed Solution

Scan active docs separately from historical roadmap/ticket material, classify hits, clean safe wording in active docs, and split ambiguous documentation areas if needed.

## Acceptance Criteria

- Active docs scanned for residue markers.
- Historical roadmap/ticket material classified separately.
- Safe active-doc wording cleanup applied.
- Larger ambiguity split into child/follow-up work.

## Verification Plan

- `rg` over active doc directories with roadmap/archive exclusions.
- Focused diff and scan after cleanup.
