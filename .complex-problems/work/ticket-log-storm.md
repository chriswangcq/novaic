# Suppress successful poll log storm

## Problem Definition

Worker claim loops emit frequent successful `/api/queue/tasks/claim` and `/api/queue/sagas/claim` logs through both internal access middleware and dependency HTTP client loggers. This contributed to disk exhaustion and Redis persistence failure.

## Proposed Solution

Quiet noisy dependency loggers during service logging bootstrap and add explicit internal access log suppression for successful hot claim paths while preserving failure logs.

## Acceptance Criteria

- `httpx`, `httpcore`, and `uvicorn.access` are warning-level after `install_service_logging()`.
- Successful task/saga claim requests are not logged by `novaic.access.internal`.
- Failed task/saga claim requests remain logged.
- Tests cover the behavior.

## Verification Plan

- Extend common logging/middleware tests.
- Run targeted `novaic-common` pytest.

## Risks

- Suppression should be path-specific and status-sensitive so real errors remain visible.

## Assumptions

- Successful high-frequency polling is operational noise; failures are signal.
