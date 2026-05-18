# Ticket: Audit session generation lifecycle and advancement

## Problem Definition

Inventory every path that creates, initializes, advances, stores, rebuilds, or defaults a session generation. Determine whether one owner controls generation changes and whether generation updates are tied to the same transaction as the related session state transition.

## Proposed Solution

Use source searches for `generation`, `next_generation`, `record_active_session`, `record_no_active`, rebuild, and decision transition code. Read the relevant slices in `session_repo.py`, `session_decision.py`, `session_ledger.py`, `session_rebuild.py`, and generation-focused tests. Record a lifecycle map and flag any hidden/default generation path.

## Acceptance Criteria

- Generation creation/advancement methods are listed with file references.
- Authoritative active generation storage is identified.
- Transaction boundaries for generation changes are classified.
- Hidden increments/defaults/fallback generation paths are either ruled out or turned into follow-up work.

## Verification Plan

Run read-only `rg` searches for generation lifecycle terms, inspect source slices, and run/identify targeted tests if available. Do not make code changes unless a concrete dangerous hidden generation path is found during execution.

## Risks

- Generation may be advanced indirectly through a helper name that does not include `generation`.
- Tests may assert behavior without naming generation, so source plus tests both need checking.

## Assumptions

- The intended active generation authority is the session state ledger, not saga context alone.
