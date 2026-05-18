# Recovery compensation finalize aggregate verification

## Problem

After source mapping and targeted fixes, P351 needs an aggregate verification pass proving recovery and compensation cannot synthesize ambiguous finalize mutation work. This belongs under P351 because individual fixes can pass while composition leaves a stale path.

## Success Criteria

- Run focused recovery and compensation tests covering generation preservation and missing-identity rejection/reroute.
- Run source/residue searches under `queue_service` for `wake_finalize`, `session_generation`, and generation defaulting patterns.
- Map each P351 success criterion to concrete code and test evidence.
- Record any remaining gap as a follow-up rather than marking P351 solved.
