# T457 Result: Session outbox ownership final verification

## Summary

Produced final session outbox ownership verification. Wake saga creation, attach input publishing, and recovery archive publishing are owned by durable session outbox rows and idempotent dispatcher/handler paths. Observed wake-created updates are applied as the observed result of `create_wake_saga` delivery, not as a separate durable effect. No dangerous bypass remains in the audited scope.

## Evidence Sources

- P458 / R447 / C473: session outbox effect inventory.
- P459 / R452 / C479: direct side-effect bypass classification and cleanup.
- P461 / R448 / C474: dispatcher direct calls classified.
- P462 / R449+R450 / C477: observed-wake residue found and removed.
- P463 / R451 / C478: final side-effect bypass guard and focused tests.
- Synthesis input: `.complex-problems/L20260516-222011/tmp/p460/ownership-final-input.txt`.

## Final Ownership Matrix

| Side Effect | Durable Owner | Delivery / Handler | Verification | Residual Bypass |
| --- | --- | --- | --- | --- |
| Wake saga creation | `tq_session_outbox` row with `effect_type=create_wake_saga` | `SessionOutboxDispatcher._publish_create_wake_saga(...)` creates saga, then `SessionObservedEventHandler.apply_wake_created(...)` applies result. | P458 inventory, P461 dispatcher classification, P463 focused tests. | None found. |
| Attach input publishing | `tq_session_outbox` row with `effect_type=publish_attach_input` | `SessionOutboxDispatcher._publish_attach_input(...)` publishes `TaskTopics.SESSION_ATTACH_INPUT` with expected wake scope/generation. | P458 inventory, P461 classification, P463 focused tests. | None found. |
| Recovery archive publishing | `tq_session_outbox` row with `effect_type=recovery_archive_scope` | `SessionOutboxDispatcher._publish_recovery_archive(...)` publishes `TaskTopics.CORTEX_SCOPE_END` with session generation, reason, and remaining stack. | P458 inventory, P461 classification, P463 focused tests. | None found. |
| Observed wake-created update | Observed result under `create_wake_saga` row | `SessionObservedEventHandler.apply_wake_created(...)` validates generation/start state and records active session or cancels stale saga. | P458 inventory and P462/P464 cleanup. | None found. Obsolete standalone observed-wake effect constant removed. |
| Generic task/saga APIs | Outside session side-effect ownership | Generic publish/saga create routes/handlers; session-owned saga types are policy-rejected. | P463 classification. | None found in session scope. |
| Saga outbox internals | Saga outbox, not session outbox | `SagaOrchestrator` internal saga outbox effect dispatch. | P463 classification. | Outside P460 session-outbox scope. |

## Changes Integrated

- Removed obsolete production `SessionOutboxDispatcher.OBSERVE_CREATE_WAKE_SAGA`.
- Updated negative guard tests to keep old effect string test-local.

## Test Evidence

- P463 focused tests: `33 passed in 0.24s`, exit `0`.
- P464 focused tests: `13 passed in 0.18s`, exit `0`.

## Conclusion

Session outbox side-effect ownership is clean in the audited scope: session side effects do not depend on direct ad hoc calls as authority; direct calls that remain are below durable outbox dispatch or outside session-specific ownership.

## Residual Risk

No P460 ownership gap remains. A full service-level smoke test is outside this final verification ticket.
