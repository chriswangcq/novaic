# P380 cross-repo stale compatibility residue guard check

## Summary

Not successful. The one-go cross-repo residue guard found and partially fixed generation-boundary issues, but the final guard still reports live implicit generation coercions in Cortex operational storage and runtime session attach state handling.

## Blocking Gaps

- `novaic-cortex/novaic_cortex/operational_store.py` still contains raw `int(generation)` in two live write paths, so the guard does not yet prove explicit generation validation at the store boundary.
- `novaic-agent-runtime/queue_service/session_repo.py` still contains `session_generation = int(current_active.get("generation") or 0)` in the attach path, so the guard does not yet prove stale or malformed active generation cannot be silently defaulted.
- The result does not contain a final guard matrix with all remaining hits classified as safe or fixed; it explicitly lists known gaps.

## Result IDs

- R369
