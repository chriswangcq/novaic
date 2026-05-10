# P002: Phase 1: Context event store substrate

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
Implement the Cortex context event source substrate: event types, event envelope, stream append/read APIs, idempotency, generation/versioning, and tests. This phase should not yet replace every caller, but it must establish the new source-of-truth substrate.

## Success Criteria
- Event schema/types are explicit and deterministic.
- Event append enforces stream identity, monotonic sequence/version, and idempotency key behavior.
- Event read supports replay by agent-root stream.
- Unit tests cover append, duplicate idempotency, ordering, invalid events, and reset/no-compat initialization.
- No hidden time/id dependencies in core event logic; clock/id providers are explicit where needed.

## Subproblems
- P007: Phase 1.1: Define ContextEvent schema and validation
- P008: Phase 1.2: Implement append-only ContextEvent store
- P009: Phase 1.3: Enforce ContextEvent idempotency and reset semantics
- P010: Phase 1.4: Verify substrate boundaries and non-integration

## Results
- R008

## Latest Check
C009

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T002: problems/P000/children/P002/tickets/T002.md
- Result R008: problems/P000/children/P002/results/R008.md
- Check C009: problems/P000/children/P002/checks/C009.md

## Follow-ups
- none
