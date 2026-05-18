# P486 Session outbox dispatcher boundary hardening check

## Summary
P486 is solved. The sanctioned session outbox side-effect boundary is documented and now has explicit guard coverage for both saga creation and session-owned queue publishes.

## Evidence
- R475 documents `session_outbox.py` as the required dispatcher boundary for `CREATE_WAKE_SAGA`, `RECOVERY_ARCHIVE_SCOPE`, and `PUBLISH_ATTACH_INPUT`.
- Existing guard asserts `.saga_orchestrator.create(` appears exactly once in `session_outbox.py`.
- New guard asserts `session_outbox.py` keeps exactly two `self.queue.publish(` calls and that `session_repo.py` / `session_wake_plan.py` do not directly publish or create sagas.
- Focused test log shows `31 passed in 0.23s` with exit code `0`.

## Criteria Map
- Document dispatcher direct effects: satisfied by the hardening artifact and R475.
- Verify saga creation and session-owned queue publishes remain limited: satisfied by existing and new guards.
- Remove or split discovered bypasses: satisfied; no bypass was found.
- Focused session outbox tests pass: satisfied by the focused test suite.

## Execution Map
- T479 was classified one-go because it was a narrow guard hardening slice.
- Execution added a static guard and ran focused session outbox/wake/attach/recovery tests.

## Stress Test
- Plausible failure mode: repository starts publishing session-owned effects directly. The new guard fails on `queue.publish(` in `session_repo.py`.
- Plausible failure mode: wake plan starts creating sagas or publishing directly. The new guard fails on `queue.publish(` or `.saga_orchestrator.create(` in `session_wake_plan.py`.
- Plausible failure mode: dispatcher gains extra queue side-effect outlets. The new exact-count guard fails.

## Residual Risk
- None for P486.

## Result IDs
- R475
