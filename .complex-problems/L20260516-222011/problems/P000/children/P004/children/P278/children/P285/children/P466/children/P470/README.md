# Duplicate session config and residue cleanup

## Problem

Clean up duplicate configuration/residue discovered during hidden-input review, including repeated literals or duplicate branch logic that can confuse future maintenance. This includes the currently observed duplicated `remaining_stack` error string if still present.

## Success Criteria

- Remove exact duplicate literals/branches in session/worker config paths where they add no semantic value.
- Keep process-boundary configuration explicit and centralized.
- Add or update focused tests/guards if the cleanup affects behavior.
- Prove no compatibility branch or stale duplicate remains in the touched area.
