# Check: P457 Cortex focused compatibility behavior tests

## Result IDs

- R441

## Status

success

## Evidence

- R441 cites the saved Cortex log and exit file.
- Exit status is `0`.
- Pytest summary is `135 passed in 1.95s`.
- The selected tests cover the Cortex behavior boundaries required by P457: lifecycle, projection, payload inspection, shell blob contract, tool/step projection, and legacy/compat guards.

## Criteria Map

- Run focused Cortex tests: satisfied by the command in R441.
- Save logs and exit status: satisfied by `cortex-focused-tests.log` and `cortex-focused-tests.exit`.
- Spawn repair if the suite fails: not needed because exit status is `0`.

## Execution Map

- Reviewed R441 and the log tail.
- Verified the log and exit file were both written.
- Performed no source changes during the check.

## Stress Test

Because T448 was one-go, I checked that the result is not merely a claimed pass: the cited log contains the pytest summary, and the exit file contains `0`.

## Residual Risk

Cortex behavior covered by the selected focused suite is clean. Any broader multi-service runtime smoke remains outside this child and belongs to parent-level verification.
