# P009 Check - Task and Saga Engines Use Effect Adapters

## Summary

P009 is solved. Task and saga action engines no longer own concrete protocol clients or direct side effects; both emit explicit named effects through reusable adapters, and guardrail tests lock that boundary.

## Evidence

- P012 result/check: task engine migrated and verified.
- P013 result/check: saga engine migrated and verified.
- P014 result/check: automated action-engine boundary guardrails added and verified.
- Focused tests passed: 10 task tests, 8 saga tests, and 21 combined boundary/regression tests.

## Criteria Map

- Task engine no longer imports/stores concrete clients -> satisfied by P012/P014.
- Saga engine no longer imports/stores concrete clients -> satisfied by P013/P014.
- Task effects cover heartbeat, idempotency, complete/fail, publish/get, saga get, and handler context -> satisfied by `TaskExecutionEffectAdapter`.
- Saga effects cover heartbeat, publish, mark launched, and mark failed -> satisfied by `SagaLaunchEffectAdapter`.
- Assembly wires adapters explicitly -> satisfied by P012/P013 code and P014 tests.
- Boundary tests reject old ownership -> satisfied by P014.

## Execution Map

- T003 -> R004: parent result summarized P012/P013/P014.
- P012 -> R001/C001: task engine migration.
- P013 -> R002/C002: saga engine migration.
- P014 -> R003/C003: boundary guards.

## Stress Test

- Old direct-client constructor arguments return -> P014 fails.
- Old direct `self.client`/`self.saga_client` ownership returns -> P014 fails.
- Adapter publish/state paths break -> P013 launch-path test fails.
- Task idempotency/retry semantics regress -> P012 focused tests fail.

## Residual Risk

- none for task/saga action engines. Health/scheduler engine migration is tracked separately by P010.

## Result IDs

- R004

## Blocking Gaps

- none
