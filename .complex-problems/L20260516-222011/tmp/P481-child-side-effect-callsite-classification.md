# Production side-effect callsite classification

## Problem

P481 needs production direct side-effect call sites classified before cleanup. The inventory has raw hits, but downstream changes need a concise table of which calls are service assembly, generic adapter, durable outbox dispatcher, session-owned effect writer, or suspicious bypass.

## Success Criteria

- Production `SagaOrchestrator.create`, `queue.publish`, task client publish, and session outbox effect call sites are listed with file references.
- Each call site is classified into an explicit category.
- Suspicious or ambiguous call sites are identified for downstream child problems.
- No source code is changed in this classification child.
