# Ticket: Classify and fix session direct side-effect bypasses

## Problem Definition

Classify direct side-effect calls found in P458 and search for additional bypasses. Fix or split any path that can publish/create session side effects without durable session outbox ownership.

## Proposed Solution

- Search runtime queue/session code for:
  - direct `SagaOrchestrator.create` / `saga_orchestrator.create`
  - direct `queue.publish`
  - direct `TaskTopics.SESSION_ATTACH_INPUT` / `TaskTopics.CORTEX_SCOPE_END`
  - old `OBSERVE_CREATE_WAKE_SAGA`
  - session state mutation after external side effects
- Classify each hit:
  - safe implementation detail below durable outbox dispatcher
  - test/guard fixture
  - risky bypass
  - removable residue
- Remove simple residue if safe to do directly; split any risky live bypass into a concrete repair child.

## Acceptance Criteria

- Direct side-effect guard artifacts are saved.
- Every P458 flag is classified.
- Additional direct publish/create hits are classified.
- Risky bypasses are fixed or split.

## Verification Plan

- Run source guards before/after any cleanup.
- Run focused tests if source is changed.
