# P485 Generic task publish route boundary decision check

## Summary
P485 is solved. The route decision is explicit: retain `/tasks/publish` as a generic queue adapter boundary, with tests guarding that it does not become a session-owned saga/effect bypass.

## Evidence
- R474 records the retain decision and rationale.
- `test_generic_task_publish_route_is_only_queue_adapter_boundary` proves the route forwards to `queue.publish` and does not call the orchestrator.
- `test_generic_task_publish_route_contains_no_session_owned_effect_logic` proves the route section contains no `subagent_wake`, `SessionOutboxDispatcher`, `build_create_wake_saga_effect`, `orchestrator`, or `saga_type`.
- Focused test log shows `6 passed in 0.22s` with exit code `0`.

## Criteria Map
- Inspect route and related direct publish behavior: satisfied by route inspection and new route tests.
- Decision recorded: satisfied by the decision artifact and R474.
- If retained, tests prove it does not bypass session-owned FSM/outbox rules: satisfied by the new behavioral and source-section guard tests.
- If changed, focused route/queue tests pass: satisfied because tests changed and passed.

## Execution Map
- T478 was classified one-go because the decision was narrow and testable.
- Execution retained the route, added explicit guards, and ran focused tests.

## Stress Test
- Plausible failure mode: route silently becomes session wake creation bypass. The source-section guard fails if session-owned wake/effect/orchestrator logic appears in the publish route.
- Plausible failure mode: route starts creating sagas. The behavioral test asserts the orchestrator is not called.

## Residual Risk
- None for P485. Session outbox direct side-effect hardening remains correctly scoped to P486.

## Result IDs
- R474
