# Check: Scope End Boundary Contract Propagation

## Summary

Success. P372 is solved by R354. The runtime-to-Cortex structural archive path now carries explicit finalize diagnostics through the saga payload, handler boundary, bridge adapter, and Cortex request contract. The check was not accepted from prose alone: runtime and Cortex focused tests were rerun after tightening the bool-generation edge case.

## Evidence

- R354 describes the implementation and verification evidence.
- Runtime focused suite passed: `61 passed`.
- Cortex focused suite passed: `25 passed`.
- Runtime adapter compile passed for changed saga/handler/bridge/recovery/outbox modules.
- Cortex API compile passed.

## Criteria Map

- `CORTEX_SCOPE_END` handler validates and forwards explicit finalize diagnostics: satisfied. Runtime handler now requires positive `session_generation`, requires `remaining_stack`, and forwards `session_generation`, `finalize_reason`, `remaining_stack`, and `round_num` to `bridge.scope_end`.
- `CortexBridge.scope_end` accepts and posts explicit diagnostics: satisfied. Bridge payload test asserts the exact `/v1/scope/end` payload and a regression test rejects bool generation before `int(True)` can silently become `1`.
- Cortex API request contract accepts explicit diagnostics: satisfied. `ScopeEndRequest` now accepts the diagnostics fields.
- Missing or non-positive generation is rejected for diagnostic archive requests: satisfied. Runtime handler tests cover missing/zero generation; Cortex request validation covers missing, zero, and bool generation.
- Non-finalize or legacy-neutral callers remain deterministic without hidden active-generation inference: satisfied. Cortex structural scope-end tests still pass without diagnostics, and no new active-generation inference was added.
- Focused runtime/Cortex contract tests pass: satisfied by the two focused suites cited above.

## Stress Test

The initial test run caught a subtle failure: Pydantic coerced `session_generation=True` to `1`, so the after-validator did not reject it. I fixed this with a pre-validator in Cortex and also hardened `CortexBridge.scope_end` with the runtime generation helper. This closes the same class of implicit-input bug on both sides of the HTTP boundary.

I also scanned the remaining `scope_end` and archive diagnostic references. The remaining no-diagnostics `ScopeEndRequest` calls are direct Cortex structural lifecycle tests, which the ticket explicitly allowed to remain valid. The runtime active and recovery archive paths now include diagnostics.

## Residual Risk

P372 does not persist the diagnostics inside Cortex archive metadata; that is intentionally owned by the sibling persistence ticket P373.

## Result IDs

- R354
