# Runtime scope lifecycle metrics cleanup check

## Summary

Success. Runtime `CortexMetrics` no longer exposes dead scope lifecycle counters, and focused metrics tests now assert only live runtime-owned counters.

## Evidence

- Static scan found no `scopes_created` or `scopes_archived` in `types.py` and focused runtime metric tests.
- Focused tests passed: `10 passed in 0.10s`.

## Criteria Map

- Runtime metrics tests no longer assert scope lifecycle counters: satisfied.
- Dead fields removed from `CortexMetrics`: satisfied.
- Focused wave4, hook-limit, and chaos metric tests pass: satisfied.

## Execution Map

- R041 removed fields from `CortexMetrics`.
- R041 migrated metric tests to runtime-owned counters and Workspace projection setup.

## Stress Test

- Static scan targeted the removed counter names across both the dataclass and focused tests.
- The focused test run includes metric shape construction, runtime skill-install metrics, read/write metrics, and repeated initialization.

## Residual Risk

- Service/API Prometheus metrics still mention scope archival by design; this does not violate the runtime `CortexMetrics` cleanup.

## Result IDs

- R041
