# Close residual live generation coercions

## Problem

The cross-repo residue guard still reports three live implicit generation coercions after T375: two in Cortex operational store write paths and one in runtime session attach active-state handling. These need to be fixed with explicit validation helpers, focused tests, and a rerun guard matrix.

## Success Criteria

- Replace the remaining raw generation coercions in `novaic-cortex/novaic_cortex/operational_store.py` with explicit non-negative generation validation.
- Replace the remaining raw active-session generation coercion in `novaic-agent-runtime/queue_service/session_repo.py` with explicit positive generation validation.
- Add focused tests that reject bool/missing/negative generation inputs where the patched boundaries can be directly exercised.
- Run focused runtime and Cortex tests covering the patched boundaries.
- Rerun cross-repo guards and provide a concise matrix classifying all remaining hits as fixed or safe.
