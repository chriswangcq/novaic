# Action Engine Effect-Plan DSL

## Problem Definition

Task, saga, health, and scheduler action engines still perform direct client/HTTP/assembler side effects. They must be moved toward explicit effect-plan objects executed by approved adapters so business execution logic is not a hidden imperative side-effect blob.

## Proposed Solution

Split this problem into smaller implementation problems:

1. Add an explicit `WorkerEffect` / `EffectPlan` / `EffectExecutor` contract and adapter helpers.
2. Migrate task and saga action engines to use effect executors instead of direct clients.
3. Migrate health and scheduler action engines to use effect executors instead of direct HTTP/assembler calls.
4. Add tests proving behavior and source boundary.

## Acceptance Criteria

- Action engines construct explicit effect objects for side effects.
- Direct protocol clients/HTTP clients/dispatch assemblers are held by adapter classes, not engines.
- Existing behavior remains covered by targeted tests.
- Source tests guard against reintroducing direct side-effect calls in engines.

## Verification Plan

- Inspect and update engine constructors, assemblies, and unit tests.
- Run task/saga/health/scheduler worker tests and new effect-plan boundary tests.
- Run compile checks over worker modules.

## Risks

- Task execution has many intertwined side effects; this phase should split if direct migration is too large.
- Tests currently instantiate engines directly with clients and will need clean updates to adapters.

## Assumptions

- No old constructor compatibility is required.
- Effect adapters may still execute effects synchronously for now; durable outbox semantics remain where they already exist.
