# Add autonomous release-controller polling loop

## Problem

The release-controller exposes `/v1/polls/once`, but the service does not yet own a periodic polling loop. Add a configurable background loop that invokes `BranchPoller` on service startup and shuts down cleanly.

## Success Criteria

- Config includes an explicit polling enable flag.
- When enabled, the FastAPI service starts a background task that calls `BranchPoller.poll_once()` every `poll_interval_seconds`.
- The loop can be disabled for tests or maintenance.
- Shutdown cancels the background task cleanly.
- Tests cover enabled and disabled behavior.
- Branch-triggered polling still cannot target prod.
