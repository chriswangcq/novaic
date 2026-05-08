# P008 Result - Effect Plan Substrate Contracts

## Summary

Implemented the generic worker effect-plan substrate as business-agnostic infrastructure under `queue_service.worker`. The substrate gives action engines an explicit plan/effect/outcome boundary so later tickets can move side effects into adapters without inventing per-worker plumbing.

## Done

- Added `queue_service/worker/effects.py` with `WorkerEffect`, `EffectPlan`, `EffectOutcome`, `EffectExecutor`, `EffectExecutionError`, and small helper functions.
- Exported the effect-plan contracts from `queue_service/worker/__init__.py`.
- Added `tests/test_pr340_worker_effect_plan.py` to verify ordered execution, missing handler failure, failure propagation, and business-agnostic imports.

## Verification

- `pytest -q tests/test_pr340_worker_effect_plan.py` passed with 4 tests.
- `python -m compileall -q queue_service/worker` passed.

## Known Gaps

- none for the substrate contract itself.
- Engine migration to the new substrate is intentionally left to child tickets P009/P010/P011.

## Artifacts

- `novaic-agent-runtime/queue_service/worker/effects.py`
- `novaic-agent-runtime/queue_service/worker/__init__.py`
- `novaic-agent-runtime/tests/test_pr340_worker_effect_plan.py`
