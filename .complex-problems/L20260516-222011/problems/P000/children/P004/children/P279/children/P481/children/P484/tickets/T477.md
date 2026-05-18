# Production side-effect callsite classification ticket

## Problem Definition

P484 must turn the P480 raw side-effect hits into a concise production call-site classification table. The output should distinguish service assembly, generic adapter/API boundaries, durable session outbox dispatchers, session-owned outbox effect writers, generic worker effect executors, tests/docs guards, and suspicious bypasses.

## Proposed Solution

Run targeted production-only `rg` queries for `SagaOrchestrator`, `.saga_orchestrator.create`, `queue.publish`, `task_client.publish`, `client.publish`, and `SessionOutboxDispatcher` in runtime/session paths. Inspect representative call sites and save a classification artifact. Do not modify source in this child.

## Acceptance Criteria

- Production direct side-effect call sites are listed with file references.
- Every listed production call site has a category and short rationale.
- Suspicious or ambiguous call sites are explicitly routed to P485/P486 or a spawned child.
- No production source code is changed.

## Verification Plan

Save raw targeted queries and classification under `.complex-problems/L20260516-222011/tmp/p484/`. Compare git status before/after excluding ledger files.

## Risks

- Over-classifying generic queue infrastructure as session bypass would create false cleanup work.
- Under-classifying route/session outbox calls would hide real bypasses.

## Assumptions

- This child is classification-only; cleanup and hardening belong to downstream P485/P486/P487.
