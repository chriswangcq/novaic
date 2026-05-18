# Check: Remaining Stack And Finalize Reason Archive Boundary

## Summary

Success. P338 is solved by R362 and child checks C372, C375, C383, and C384. The finalize/archive diagnostics boundary now binds reason, stack, and generation to explicit session/scope identity.

## Evidence

- R362 summarizes the full child tree.
- P367/P370 hardened stale finalize assertions.
- P368 fixed runtime-to-Cortex archive diagnostics binding and persistence.
- P369 fixed repo-level bool generation coercion and aggregate-verified focused suites.

## Criteria Map

- Map where finalize reason, ended-at, and remaining stack are recorded: satisfied by P366/P367/P369 residue review.
- Records tied to explicit saga/scope/generation identity: satisfied through session finalize metadata, wake-finalize payloads, runtime handler, bridge, recovery archive, and Cortex nested diagnostics.
- Fix stale active lookup/generation risks: satisfied by stale finalize rejection coverage and bool-generation coercion fixes.
- Tests prove stale finalize cannot archive remaining stack for newer wake: satisfied by hardened `test_pr254_finalize_ownership.py`.
- Tests prove valid finalize records reason/stack for intended generation: satisfied by runtime and Cortex focused tests.

## Execution Map

The work was split instead of one-go: mapping, stale finalize audit, Cortex archive binding/persistence, and aggregate verification.

## Stress Test

The check explicitly covered historical partial-fix risks: handler-only validation without repo validation, propagation without persistence, and semantic/diagnostic stack collision.

## Residual Risk

None for P338.

## Result IDs

- R362
