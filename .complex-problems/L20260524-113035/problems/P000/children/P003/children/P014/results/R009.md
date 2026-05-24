# P014 Result

## Summary

Added release-controller Compose runtime integration as an internal control-plane service.

## Done

- Added `docker/release-controller/compose.yaml`.
- Added `docker/release-controller/env.sample`.
- Compose service is named `release_controller`.
- Image is parameterized through `NOVAIC_RELEASE_CONTROLLER_IMAGE`.
- Runtime config is passed through `NOVAIC_RELEASE_CONTROLLER_CONFIG`.
- Host config, state dir, release root, worktree, and Docker socket mounts are explicit.
- Host port binds only to `127.0.0.1`.
- No Nginx route or public domain routing was added.

## Verification

- `docker-compose --env-file docker/release-controller/env.sample -f docker/release-controller/compose.yaml config`
  - Rendered successfully.
  - Rendered port binding is `host_ip: 127.0.0.1`, `published: "19880"`.
- `PYTHONPATH=novaic-release-controller python3 -m pytest novaic-release-controller/tests -q`
  - Passed: 31 tests.
- `rg -n "server_name|staging-api|api\\.gradievo|nginx|proxy_pass" docker/release-controller docs/architecture/release-controller.md`
  - No release-controller Nginx/public routing was found under `docker/release-controller`.

## Known Gaps

- Deploy script wiring remains assigned to P015.
- Real container startup remains assigned to deployment verification.

## Artifacts

- `docker/release-controller/compose.yaml`
- `docker/release-controller/env.sample`
