# P014 Check - Task/Saga Engine Boundary Guards

## Summary

P014 is solved. Automated tests now lock the P012/P013 effect-adapter boundary so old direct-client ownership cannot quietly return to task/saga action engines.

## Evidence

- `tests/test_pr340_action_engine_effect_boundaries.py` enforces AST/source guardrails for both action engines and worker assembly.
- Focused task/saga regression suite passed with 21 tests.
- Compile check passed for worker modules and the new guardrail test.

## Criteria Map

- Reject concrete client imports -> satisfied by `_imported_modules` assertions.
- Reject old constructor parameters -> satisfied by `__init__` AST arg checks.
- Reject self-owned protocol clients -> satisfied by self attribute assignment checks.
- Reject direct self-client protocol calls -> satisfied by AST call checks.
- Assert assembly adapter wiring -> satisfied by explicit wiring assertions in `worker_assemblies.py`.

## Execution Map

- T006 -> R003: added boundary guard tests and verified focused worker suite.

## Stress Test

- Regression attempt: adding `client`, `saga_client`, `business_client`, or URL args back to engine constructors will fail tests.
- Regression attempt: importing `task_queue.client` in action engines will fail tests.
- Regression attempt: wiring engines without the adapter executor will fail tests.

## Residual Risk

- none for task/saga engine guardrails.

## Result IDs

- R003

## Blocking Gaps

- none
