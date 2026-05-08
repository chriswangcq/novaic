# P008 Check - Effect Plan Substrate Contracts

## Summary

P008 is solved. The infrastructure-level effect-plan contract exists, is exported as reusable worker substrate, and is tested without importing task, saga, session, or business modules.

## Evidence

- `novaic-agent-runtime/queue_service/worker/effects.py` defines the reusable effect/action boundary contracts.
- `novaic-agent-runtime/queue_service/worker/__init__.py` exports the new contracts for worker engines and assemblies.
- `novaic-agent-runtime/tests/test_pr340_worker_effect_plan.py` verifies ordered execution, missing handler errors, failure propagation, and business-agnostic imports.
- `pytest -q tests/test_pr340_worker_effect_plan.py` passed.
- `python -m compileall -q queue_service/worker` passed.

## Criteria Map

- Generic effect contracts exist -> satisfied by `WorkerEffect`, `EffectPlan`, and `EffectOutcome`.
- Effects are executed through explicit adapters/handlers -> satisfied by `EffectExecutor`.
- Failure is explicit and testable -> satisfied by `EffectExecutionError`, `EffectOutcome.failed`, and tests.
- Substrate stays business-agnostic -> satisfied by import/source guard test.

## Execution Map

- T002 -> R000: added the substrate, exports, tests, and verification.

## Stress Test

- Missing handler -> `EffectExecutionError` is raised instead of silently skipping a side effect.
- Adapter returns failure -> `execute_effect` rejects the outcome instead of leaking a partial success.
- Future accidental business import -> test fails on forbidden imports/text in `effects.py`.

## Residual Risk

- none for P008. Engine migration is intentionally covered by P009/P010/P011.

## Result IDs

- R000

## Blocking Gaps

- none
