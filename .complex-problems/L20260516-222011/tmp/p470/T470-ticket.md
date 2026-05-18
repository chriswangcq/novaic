# Duplicate session config and residue cleanup ticket

## Problem Definition

P470 must remove duplicate literals/obvious residue in session/worker config paths. The known candidate is a duplicated `remaining_stack` error string in `session_outbox.py`.

## Proposed Solution

Run a small duplicate/residue guard over session outbox/config areas, fix exact no-semantic-value duplicates, and verify with focused tests/guards. Do not introduce compatibility branches.

## Acceptance Criteria

- The duplicated `remaining_stack` error string is removed if still present.
- Any other exact duplicate/residue in the focused session config/outbox area is either fixed or explicitly classified as intentional.
- Focused session outbox/residue tests pass.
- A source guard proves the duplicate string pattern no longer exists.

## Verification Plan

Run source guard before/after, focused pytest for session outbox/residue tests, and save logs under `.complex-problems/L20260516-222011/tmp/p470/`.

## Risks

- Over-broad deduplication could change error semantics; only exact obvious duplicate text should be touched.

## Assumptions

- This problem is small and can be one-go if the duplicate string is the only production hit.
