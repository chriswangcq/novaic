# Deploy repaired backend services

## Problem Definition

The repaired runtime/Cortex code must be deployed to production.

## Proposed Solution

Use the repository deployment script to sync backend services and restart via the managed `start.sh` path.

## Acceptance Criteria

- Deployment command succeeds.
- Fresh-smoke log check succeeds.
- `./deploy status` shows required services and workers up.

## Verification Plan

- Run `./deploy services`.
- Run `./deploy status`.
- Record command outcomes.

## Risks

- Deployment restarts all backend services.

## Assumptions

- `./deploy services` is the supported backend deployment path for changes touching both runtime and Cortex.
