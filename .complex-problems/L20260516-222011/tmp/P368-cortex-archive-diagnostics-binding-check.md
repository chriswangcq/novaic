# Check: Cortex Archive Diagnostics Binding

## Summary

Success. P368 is solved by R360 and children P371-P374. The archive diagnostics path now uses explicit payload identity end-to-end and persists valid diagnostics without relying on active lookup for generation.

## Evidence

- R360 summarizes closed child problems.
- P372/C377 proves runtime boundary propagation and validation.
- P373/C381 proves Cortex persistence.
- P374/C382 proves aggregate runtime/Cortex compile, tests, and residue scans.

## Criteria Map

- Verify/fix runtime handler, wake-finalize payload builders, and bridge calls: satisfied by P372.
- Tests prove stale or missing generation cannot archive: satisfied by runtime handler/bridge/Cortex request validation tests.
- Tests prove valid archive records intended reason/generation metadata: satisfied by `archive_diagnostics` persistence test.
- No direct archive path uses inferred active generation: satisfied by source scans and request-only diagnostics persistence.

## Execution Map

Split execution covered source mapping, boundary propagation, Cortex persistence, and aggregate verification. This prevents the prior class of half-integrated change where new code exists but active paths stay old.

## Stress Test

I checked the two highest-risk failure modes: bool generation coercion (`True -> 1`) and `remaining_stack` shape collision. Both were explicitly fixed/tested: bool is rejected before coercion, and diagnostic stack is nested under `archive_diagnostics`.

## Residual Risk

None for P368.

## Result IDs

- R360
