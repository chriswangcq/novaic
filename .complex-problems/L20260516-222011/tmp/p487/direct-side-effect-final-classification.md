# Direct side-effect bypass final classification

## Final Guard Summary

- Guard artifact: `.complex-problems/L20260516-222011/tmp/p487/direct-side-effect-final-guards.txt`
- Raw line count: `73`

## Remaining Production Hits

All remaining production hits are classified:

- `queue_service/main.py` and `task_queue/workers/assembly_factories.py`: service/worker dependency assembly boundaries.
- `queue_service/routes.py` factory `SagaOrchestrator(...)`: route factory dependency fallback; not a side-effect call.
- `queue_service/routes.py:219` `queue.publish(...)`: retained generic task queue adapter boundary, guarded by P485 tests.
- `queue_service/session_outbox.py:185/212/255`: sanctioned durable session outbox dispatcher side-effect boundary, guarded by P486 tests.
- `task_queue/workers/saga_effects.py:35` and `task_queue/workers/task_effects.py:84`: generic worker effect executor boundaries.
- `queue_service/session_repo.py` and `session_wake_plan.py`: build/write durable outbox effects, no direct publish or saga creation.
- `queue_service/saga_repo.py` compensation/suspected-dead effect builders: saga-owned effect construction, not direct session dispatch.
- `queue_service/queue_db.py` and `task_queue/client.py`: examples/docs for generic queue APIs.

## Test / Docs Separation

P487 uses production-only guards. Test fixture coverage is separately represented by the focused pytest suite.

## Verification

- Focused tests: `37 passed in 0.37s`.
- No unclassified dangerous direct side-effect bypass remains in this P481 scope.
