# Check: P459 session direct side-effect bypass classification

## Result IDs

- R452

## Status

success

## Evidence

- R452 aggregates P461, P462/P464, and P463.
- A real production residue was found and removed, rather than classified away.
- Final side-effect bypass guard and focused tests passed.

## Criteria Map

- Search direct side-effect bypasses: satisfied by P461/P463 guards.
- Classify each hit: satisfied by P461 and P463 classifications.
- Remove simple residue: satisfied by P462/P464 observed-wake cleanup.
- Split risky live bypasses: not needed beyond P464; no dangerous live bypass remains.

## Execution Map

- Reviewed R452 and child checks.
- Confirmed the not-success path in P462 was repaired before parent success.
- Performed no new implementation during this check.

## Stress Test

This subtree caught an actual stale production constant, so I did not treat “tests pass” as enough. Success depends on both code cleanup and final broad guard classification.

## Residual Risk

No P459 gap remains.
