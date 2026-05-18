# Generic task publish route boundary decision result

## Summary
Completed P485. The generic `/tasks/publish` route is retained as an internal queue adapter boundary, and focused tests now guard that it forwards only to `queue.publish` and does not contain session-owned wake/effect logic.

## Done
- Inspected `queue_service/routes.py` and existing saga creation boundary policy tests.
- Decided to retain `/tasks/publish` as generic queue infrastructure.
- Added tests proving the route does not call the orchestrator and does not contain session-owned effect construction logic.
- Saved the decision artifact and focused test log.

## Verification
- `python -m pytest tests/test_saga_creation_policy_boundary.py`
- Result: `6 passed in 0.22s`.

## Known Gaps
- None for P485. Session outbox direct side-effect hardening remains owned by P486.

## Artifacts
- `.complex-problems/L20260516-222011/tmp/p485/generic-task-publish-route-boundary-decision.md`
- `.complex-problems/L20260516-222011/tmp/p485/saga-creation-policy-boundary-tests.log`
- `.complex-problems/L20260516-222011/tmp/p485/saga-creation-policy-boundary-tests.exit`
- `novaic-agent-runtime/tests/test_saga_creation_policy_boundary.py`
