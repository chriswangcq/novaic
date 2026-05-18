# T456 Result: Side-effect bypass final guard

## Summary

Ran final session side-effect bypass guards and focused outbox tests after observed-wake cleanup. No dangerous live bypass remains in the checked session side-effect ownership scope. Focused tests passed with `33 passed`.

## Artifacts

- Guard output: `.complex-problems/L20260516-222011/tmp/p463/side-effect-bypass-final-guard.txt` (`92` lines).
- Focused test log: `.complex-problems/L20260516-222011/tmp/p463/side-effect-bypass-focused-tests.log`.
- Focused test exit: `.complex-problems/L20260516-222011/tmp/p463/side-effect-bypass-focused-tests.exit` = `0`.

## Test Evidence

```text
33 passed in 0.24s
```

Covered tests:

- `tests/test_pr251_wake_creation_outbox_cutover.py`
- `tests/test_pr248_attach_outbox_cutover.py`
- `tests/test_pr247_recovery_outbox_cutover.py`
- `tests/test_pr249_observed_wake_outbox_cleanup.py`
- `tests/test_pr250_observed_wake_effect_rename.py`
- `tests/test_pr267_session_outbox_effect_boundary.py`

## Retained Hit Classification

| Hit Category | Representative References | Classification |
| --- | --- | --- |
| Generic task publish route | `queue_service/routes.py:216-227` | Generic task queue API, not session side-effect ownership. |
| Generic saga create route | `queue_service/routes.py:365-377` | Safe generic API with `reject_session_owned_saga_type(...)`; session-owned wake saga creation cannot bypass session outbox through this route. |
| Generic saga trigger handler | `task_queue/handlers/saga_handlers.py:59-75` | Generic handler with `validate_saga_trigger_type(...)`; not a session-specific bypass. |
| Session dispatcher direct calls | `session_outbox.py:185`, `session_outbox.py:212`, `session_outbox.py:255` | Already classified in P461 as safe implementation details below durable session outbox rows. |
| Wake finalize saga definition | `task_queue/sagas/wake_finalize.py:131-141` | Saga step declaration, not a direct publish bypass. |
| Saga outbox internal effect | `queue_service/saga_repo.py:1260-1265` | Saga outbox-owned internal effect, not session outbox bypass; separate saga outbox model. |
| Worker assembly/main construction | `queue_service/main.py`, `task_queue/workers/assembly_factories.py` | Dependency assembly only. |
| Observed-wake obsolete production string | final guard section empty | Removed by P464/P462. |

## Conclusion

Wake saga creation, attach input publishing, and recovery archive publishing are owned by `tq_session_outbox` rows plus `SessionOutboxDispatcher`. Retained direct calls are either below the dispatcher, generic non-session APIs with policy guards, saga-outbox internals, or assembly/test code.

## Changes

No source changes were made by P463. It verified the cleanup performed in P464 and classified retained guard hits.

## Residual Risk

No P463 side-effect bypass gap remains in the checked scope.
