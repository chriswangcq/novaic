# Direct side-effect bypass cleanup ticket

## Problem Definition

P481 must classify and clean up direct side-effect call sites in queue/session/runtime paths. The target surface is direct `SagaOrchestrator.create`, `queue.publish`, task client publish, and session outbox effect dispatching that could bypass explicit FSM/outbox ownership.

## Proposed Solution

Use the P480 inventory as the starting point, then inspect each production side-effect class directly. Keep required service assembly, generic worker effect executor, public/internal task queue adapter, and durable session outbox dispatcher boundaries. Remove or tighten any high-confidence bypass that performs session-owned effects outside FSM/outbox. If a candidate is architecturally ambiguous, spawn a smaller child problem rather than deleting it speculatively. Run focused outbox/session tests if source changes.

## Acceptance Criteria

- Production direct side-effect call sites are classified with file references.
- Required side-effect boundaries are documented and retained.
- High-confidence stale bypasses are removed or converted to explicit FSM/outbox effects.
- Ambiguous call sites are spawned as smaller child problems.
- Focused side-effect/session outbox tests pass after any source change.

## Verification Plan

Inspect direct side-effect hits from P480 plus fresh targeted `rg` queries. If changes occur, run focused tests around session outbox, wake creation outbox cutover, attach outbox cutover, recovery outbox cutover, and saga/task worker effect execution.

## Risks

- Public/internal task queue publish APIs may look like bypasses but are legitimate adapter boundaries.
- Session outbox dispatcher is intentionally the place where durable effects become external calls.
- Removing a generic worker effect executor would break the FSM substrate rather than clean business logic.

## Assumptions

- Cleanup should focus on session-owned bypasses, not generic queue/task infrastructure that is explicitly an adapter boundary.
