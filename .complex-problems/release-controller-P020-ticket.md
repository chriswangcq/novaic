# Autonomous polling loop implementation

## Problem Definition

`poll_interval_seconds` exists in config, but the service never uses it. The controller needs a service-owned polling loop that can be enabled explicitly and stopped cleanly.

## Proposed Solution

Add a small runtime component that:

- starts an asyncio background task during FastAPI lifespan when polling is enabled
- calls `BranchPoller.poll_once()` immediately and then every configured interval
- records recent loop outcomes/errors for `/v1/status`
- cancels cleanly on shutdown
- keeps polling disabled unless explicitly enabled in config

## Acceptance Criteria

- Config supports an explicit `polling_enabled` boolean.
- Disabled polling starts no background task.
- Enabled polling starts a task and calls the poller.
- Shutdown cancels the task cleanly.
- Status exposes polling state.
- Tests cover disabled and enabled behavior.

## Verification Plan

- Add focused tests using a fake branch provider and short poll interval.
- Run release-controller tests.
- Run release-controller CI guard.

## Risks

- Background tasks can become flaky in tests if sleep intervals are not controlled; keep tests short and deterministic.

## Assumptions

- Default polling remains disabled until the API-host runtime config explicitly enables it.
