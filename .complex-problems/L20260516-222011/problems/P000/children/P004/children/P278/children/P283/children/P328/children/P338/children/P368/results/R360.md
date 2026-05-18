# Cortex Archive Diagnostics Binding Parent Result

## Summary

P368 completed through child problems P371-P374. The Cortex scope archive path now binds finalize diagnostics to explicit runtime payload identity instead of inferred active lookup, and persists valid diagnostics to Cortex context events.

## Child Results

- P371 source-mapped archive diagnostics flow.
- P372 propagated explicit diagnostics through wake-finalize saga, runtime handler, bridge, recovery archive outbox, and Cortex request validation.
- P373 persisted diagnostics in Cortex `WakeArchived` events under nested `archive_diagnostics`.
- P374 aggregate-verified runtime/Cortex tests, compile checks, and residue scans.

## Final State

- Missing or non-positive `session_generation` is rejected before runtime archive.
- Bool `session_generation` is rejected in both runtime bridge and Cortex request validation.
- Runtime active and recovery archive paths carry explicit `session_generation`, `finalize_reason`, diagnostic `remaining_stack`, and `round_num`.
- Cortex persists diagnostics as nested `archive_diagnostics` and preserves top-level semantic `remaining_stack` for context projection.
- No direct Cortex archive diagnostics path synthesizes generation from active lookup.

## Verification

- Runtime focused suite: 61 passed.
- Cortex focused suite: 80 passed.
- Source scans confirmed no active-generation inference in Cortex archive diagnostics and no semantic/diagnostic `remaining_stack` conflation.

## Residual Note

No follow-up is needed for P368.
