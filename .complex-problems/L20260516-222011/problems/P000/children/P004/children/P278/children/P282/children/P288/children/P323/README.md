# Audit rebuild and pending projection writers

## Problem

Map session rebuild and pending-input projection writers to verify they update the intended session ledger/state model and cannot drift as independent authoritative state.

## Success Criteria

- Rebuild/projection functions are listed with file references.
- Their source tables/events and target state/projection are identified.
- Any independent cache/view that can drift from session ledger authority is flagged.
