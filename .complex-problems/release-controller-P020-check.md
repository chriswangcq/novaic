# P020 Success Check

## Summary

P020 is successful. The service now has an explicit, test-covered autonomous polling loop that is disabled by default and visible through `/v1/status`.

## Evidence

- `polling_enabled` is parsed and validated in `ControllerConfig`.
- `BranchPollingLoop` starts only when enabled and cancels on shutdown.
- FastAPI lifespan starts/stops the loop.
- `/v1/status` reports polling enabled/running/iteration/outcome state.
- Tests cover enabled behavior, disabled behavior, and config validation.

## Criteria Map

- Config includes explicit polling enable flag: satisfied by `polling_enabled`.
- Enabled service starts a background task: satisfied by lifecycle test observing `iteration_count >= 1`.
- Disabled loop starts no task: satisfied by disabled lifecycle test.
- Shutdown cancels cleanly: satisfied by TestClient lifespan exit without leaked task failure.
- Tests cover enabled and disabled behavior: satisfied.
- Branch-triggered polling cannot target prod: satisfied by unchanged planner/model prod guards and existing CI guard.

## Execution Map

- Added polling runtime component.
- Added config field and sample config.
- Integrated the component into the HTTP service lifecycle.
- Extended tests and ran guard coverage.

## Stress Test

- The loop remains opt-in, so deployment cannot accidentally start branch automation until runtime config explicitly enables it.
- The test loop runs immediately and with a one-second interval, proving the first poll does not require waiting for the first interval.

## Residual Risk

- Host deployment and enabling are intentionally left to P021.

## Result IDs

- R019
