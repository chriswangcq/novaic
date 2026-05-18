# Active Architecture Docs Residue Scan Ticket

## Problem Definition

Active architecture docs may still describe legacy, fallback, compatibility, or migration behavior as current guidance.

## Proposed Solution

Scan active architecture docs, classify hits, clean safe stale wording, and rescan.

## Acceptance Criteria

- Architecture docs scanned.
- Hits classified.
- Safe stale active guidance cleaned.
- Rescan recorded.

## Verification Plan

- `rg` over `docs/architecture` and related active architecture docs.
- Focused diff and rescan.
