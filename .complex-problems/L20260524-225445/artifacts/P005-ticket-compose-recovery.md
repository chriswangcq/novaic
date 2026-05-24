# Add namespace-scoped Compose release recovery

## Problem Definition

The final WebRTC release image path can fail when Docker Compose leaves a namespace project in a corrupt recreate state. The observed staging failure leaves renamed half-created containers and makes `docker compose ps -a` fail, which blocks Release Controller from completing staging and prevents prod promotion.

## Proposed Solution

Make the `services-image` deployment path recovery-safe by adding a namespace-scoped Compose project reset helper and using it only as a retry path when `docker compose up -d --no-build --remove-orphans` fails. The helper should target the compose project derived from the requested namespace, clear only that project's containers through Compose labels and project-name patterns, then retry the same immutable image deployment. After patching, publish the deploy script through the normal main branch path, rerun Release Controller for the final commit, and promote prod from the passing staging images.

## Acceptance Criteria

- `deploy services-image <namespace> <image>` retries a failed `docker compose up` after a namespace-scoped project reset.
- Cleanup targets only `novaic-<namespace>` containers and does not touch prod when recovering staging.
- The final commit reaches staging through Release Controller.
- Staging smoke passes.
- Prod is promoted through Release Controller from the same final commit images.
- Prod and staging release pointers both reference the final parent commit.

## Verification Plan

Run shell syntax checks, run existing release-controller tests/lints if changed behavior needs coverage, deploy the final commit through Release Controller, verify `/api/turn/credentials` on prod and staging, and query Release Controller status for prod/staging pointers.

## Risks

- A too-broad cleanup command could affect the wrong namespace.
- Retrying after every failure could mask application startup bugs if not scoped only to Compose state recovery.
- The remote staging project may already be partially down and need the recovery helper to remove both normal and renamed Compose containers.

## Assumptions

- Staging may be reset during this recovery.
- Prod must not be reset until staging passes and prod is intentionally promoted.
- Release Controller remains the owner of image release execution.
