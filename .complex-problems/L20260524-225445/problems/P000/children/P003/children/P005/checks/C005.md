# P005 compose recovery success check

## Summary

P005 is successful. The deployment path now has namespace-scoped recovery and health-based convergence, and the final commit was released to staging and promoted to prod through Release Controller.

## Evidence

- `bash -n deploy` passed locally after the recovery changes.
- `python3 -m pytest -q scripts/ci/test_release_controller_ci.py` passed locally with `9 passed`.
- `python3 scripts/ci/lint_immutable_image_workflows.py` passed locally.
- Release Controller staging run `20260524-154416-main-b6ba02e4165b` succeeded.
- Release Controller prod promotion run `20260524-154727-promote-prod-staging-b6ba02e4165b` succeeded.
- Release Controller current pointers show both prod and staging on commit `b6ba02e4165b9ad3d7754d2b9227740aaf13b380`.

## Criteria Map

- `services-image` retries a failed `docker compose up` after namespace-scoped reset: satisfied by `reset_api_backend_compose_project()` and the retry branch in `deploy_services_image()`.
- Cleanup targets only `novaic-<namespace>`: satisfied by label filter `com.docker.compose.project=novaic-$namespace`.
- Final commit reaches staging through Release Controller: satisfied by run `20260524-154416-main-b6ba02e4165b`.
- Staging smoke passes: satisfied by the successful `smoke-staging` step in that run.
- Prod is promoted from the same images: satisfied by promotion run `20260524-154727-promote-prod-staging-b6ba02e4165b`.
- Prod and staging release pointers both reference the final parent commit: satisfied by Release Controller status after promotion.

## Execution Map

- Result R004 records the code changes, local validation, staging run, prod promotion run, and live endpoint checks.

## Stress Test

- The failure mode reproduced during deployment: Docker Compose returned non-zero because of stale or racing container handles, while services later converged healthy. The new deploy path tolerated this exact condition by checking key service health before failing the release.
- A true application failure still fails because the health wait returns non-zero when key services do not become healthy.

## Residual Risk

- Docker Compose may still emit noisy transient errors during recreate, but the release result now follows health convergence rather than raw transient output.
- The reset helper is intentionally scoped to one namespace project; it does not clean cross-namespace or host infrastructure state.

## Result IDs

- R004
