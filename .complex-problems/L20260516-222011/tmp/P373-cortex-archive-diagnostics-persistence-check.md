# Check: Cortex Archive Diagnostics Persistence

## Summary

Success. P373 is solved by R358 and child checks C378-C380. Cortex now persists explicit runtime finalize diagnostics without conflating them with semantic context-projection stack data.

## Evidence

- R358 summarizes P375/P376/P377.
- C378 validates the source map and nested diagnostics shape.
- C379 validates implementation and focused Cortex tests.
- C380 validates aggregate runtime/Cortex tests and residue scans.

## Criteria Map

- Cortex writes explicit `finalize_reason`, `session_generation`, and diagnostic remaining-stack metadata: satisfied via nested `archive_diagnostics`.
- Archive logic does not synthesize finalize generation from active lookup: satisfied by request-only diagnostics and residue scan.
- Missing/invalid generation cannot produce diagnostic archive metadata: satisfied by `ScopeEndRequest` validation tests and runtime handler tests.
- Focused Cortex tests prove valid archive metadata and invalid generation rejection: satisfied.

## Execution Map

The split ticket was executed through source mapping, implementation, and aggregate verification children. Production changes were limited to Cortex API/writer and runtime bridge validation hardening from P372.

## Stress Test

The critical risk was overloading `remaining_stack`. The final shape keeps semantic `WakeArchived.payload.remaining_stack` as the list consumed by projection and adds runtime diagnostics under `WakeArchived.payload.archive_diagnostics`.

## Residual Risk

None for P373. P374 owns parent-level aggregate verification for all P368 children.

## Result IDs

- R358
