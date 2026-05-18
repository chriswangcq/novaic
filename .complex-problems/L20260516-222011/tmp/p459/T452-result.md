# T452 Result: Session direct side-effect bypass classification

## Summary

Completed session direct side-effect bypass classification. Dispatcher-internal direct calls are safe below durable outbox ownership, obsolete observed-wake production residue was removed, and the final side-effect bypass guard found no dangerous live bypass in checked scope.

## Child Results

- P461 / R448 / C474: dispatcher direct calls classified as safe implementation details below durable outbox rows.
- P462 / R449+R450 / C477: observed-wake outbox residue found, removed through P464, and rechecked successful.
- P463 / R451 / C478: final side-effect bypass guard passed; focused tests `33 passed`.

## Changes

- Removed `SessionOutboxDispatcher.OBSERVE_CREATE_WAKE_SAGA` from production source.
- Updated observed-wake negative tests to use test-local `OLD_OBSERVE_CREATE_WAKE_SAGA_EFFECT`.

## Evidence

- P461 guard: `.complex-problems/L20260516-222011/tmp/p461/dispatcher-direct-call-guard.txt`.
- P464 after guard: `.complex-problems/L20260516-222011/tmp/p464/observe-wake-after.txt`.
- P463 final guard: `.complex-problems/L20260516-222011/tmp/p463/side-effect-bypass-final-guard.txt`.
- P463 focused tests: `33 passed in 0.24s`.
- P464 focused tests: `13 passed in 0.18s`.

## Classification

- Direct calls inside `SessionOutboxDispatcher`: safe below durable row ownership.
- Old observed-wake effect constant in production: removed residue.
- Generic routes/handlers caught by broad guard: safe non-session APIs with policy validation, not session side-effect bypasses.
- Saga outbox internals: separate durable saga outbox model, not session outbox bypass.

## Residual Risk

No P459 direct side-effect bypass gap remains in checked scope.
