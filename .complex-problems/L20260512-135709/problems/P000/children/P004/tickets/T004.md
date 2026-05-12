# Deploy and verify production repair

## Problem Definition

Code fixes for FSM replay and log storm suppression must be tested, deployed, and verified in production.

## Proposed Solution

Run targeted tests, deploy runtime/common services, then inspect production disk, Redis, queue session state, recent tasks, and logs.

## Acceptance Criteria

- Targeted tests pass before deployment.
- Deployment completes.
- Production session state is clean after deployment.
- Disk and Redis remain healthy.
- Recent logs no longer show successful claim poll spam at INFO.

## Verification Plan

- Run runtime and common targeted tests.
- Run `./deploy runtime`.
- Query production DB/Redis/disk and tail relevant logs.

## Risks

- Deployment may restart services while a wake is running; verification should check final queue state.

## Assumptions

- `./deploy runtime` deploys both runtime and shared common package changes used by services.
