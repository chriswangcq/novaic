# Reference and Runbook Docs Residue Scan Ticket

## Problem Definition

Reference and runbook docs may contain stale operational instructions around legacy paths, compatibility branches, fallback behavior, or migrations.

## Proposed Solution

Scan active reference/runbook docs, classify hits, clean safe stale operational wording, and rescan.

## Acceptance Criteria

- Reference/runbook docs scanned.
- Hits classified.
- Safe stale operational wording cleaned.
- Verification rescan recorded.

## Verification Plan

- `rg` over `docs/reference` and `docs/runbooks` if present.
- Focused diff and rescan.
