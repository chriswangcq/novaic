# React saga decision config model ticket

## Problem Definition

React saga decision callbacks need a small explicit config abstraction so default values can originate from `ServiceConfig` at a boundary while tests and callers can pass deterministic values without global monkeypatching.

## Proposed Solution

Create a focused config dataclass in the react contract layer, likely `ReactSagaDecisionConfig`, containing `max_rounds_before_force_finalize` and `max_stack_hold_retries`. Provide a default factory that reads `ServiceConfig` outside pure decision functions. This model will be consumed by P476 wiring.

## Acceptance Criteria

- A typed config object exists in an appropriate contract/module location.
- The object contains all saga decision limits currently read from `ServiceConfig`.
- There is a default provider/factory that can be replaced by tests or callers.
- No behavior is wired yet beyond adding the model; wiring belongs to P476.

## Verification Plan

Run syntax/import checks for the modified module and inspect that the config model imports do not create circular dependencies.

## Risks

- Importing `ServiceConfig` from the wrong module can create a contract-layer dependency on common config.
- A config model with defaults baked into field values would still hide inputs.

## Assumptions

- It is acceptable for the default provider to live in the saga adapter layer if importing `ServiceConfig` into contracts is too leaky.
