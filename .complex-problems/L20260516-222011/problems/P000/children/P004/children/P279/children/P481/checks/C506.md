# P481 Direct side-effect bypass cleanup check

## Summary
P481 is solved. Direct side-effect call sites were classified, required adapter/outbox boundaries were retained with guards, no high-confidence stale bypass remained, and final focused tests passed.

## Evidence
- P484/R473/C502 classified production side-effect call sites with file references.
- P485/R474/C503 retained `/tasks/publish` as a generic queue adapter and added tests proving it does not call the orchestrator or contain session-owned effect logic.
- P486/R475/C504 hardened the session outbox dispatcher boundary with tests proving repository/wake-plan code does not directly publish or create sagas.
- P487/R476/C505 reran final production guards and focused tests; all remaining production hits are classified.

## Criteria Map
- Direct side-effect call sites classified: satisfied by P484 and P487 classification artifacts.
- Required adapter/outbox dispatcher boundaries documented and retained: satisfied by P485/P486 decisions and guards.
- High-confidence stale bypasses removed or replaced: satisfied; no stale bypass was found after classification/hardening.
- Ambiguous call sites split: satisfied; `/tasks/publish` and session outbox outlet were handled by P485/P486.
- Focused tests pass after source changes: satisfied by P485/P486/P487 logs.

## Execution Map
- T476 split into P484, P485, P486, and P487.
- P484 classified production call sites.
- P485 added generic task publish route guards.
- P486 added session outbox side-effect boundary guards.
- P487 verified final production guards and focused tests.

## Stress Test
- Plausible failure mode: generic route publish remains an unguarded bypass. P485 added behavior/source-section guards.
- Plausible failure mode: repository or wake plan directly publishes session-owned side effects later. P486 added static guards.
- Plausible failure mode: final production guard still has raw unclassified hits. P487 classified every remaining production bucket.

## Residual Risk
- Non-blocking: final verification remains pattern based, but it is paired with explicit route/outbox guard tests and focused behavior tests.

## Result IDs
- R477
