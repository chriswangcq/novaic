# Check: P456 runtime focused compatibility behavior tests

## Result IDs

- R440

## Status

success

## Evidence

- R440 cites the saved runtime log and exit file.
- Exit status is `0`.
- Pytest summary is `100 passed in 0.59s`.
- The selected tests cover attach/generation, outbox cutover, finalize ownership, session-ended notifications, suspected-dead recovery, session-state SSOT, active-session removal, legacy cleanup, explicit contracts, historical image guard, and shell output contract.

## Criteria Map

- Run focused runtime tests: satisfied by the command in R440.
- Save logs and exit status: satisfied by `runtime-focused-tests.log` and `runtime-focused-tests.exit`.
- Spawn repair if the suite fails: not needed because exit status is `0`.

## Execution Map

- Reviewed R440 and the log tail.
- Verified the initial wrapper bug was corrected and the final evidence includes both pytest summary and exit file.
- Performed no source changes during the check.

## Stress Test

Because T447 was one-go, I checked the evidence for false success: the first attempt had a wrapper issue, but the final rerun uses a corrected wrapper, has an exit file, and reports `100 passed`. This is sufficient for P456.

## Residual Risk

Runtime behavior covered by the selected focused suite is clean. Broader end-to-end behavior is outside this child and remains part of parent-level verification.
