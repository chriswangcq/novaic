# P015 Result

## Summary

Added image-based release-controller deployment support to the top-level `deploy` script.

## Done

- Added release-controller constants for remote Compose directory, compose file, env file, and image ref.
- Extended `normalize_image_ref` with `release-controller`.
- Added `sync_release_controller_compose_package`.
- Added `write_release_controller_env`.
- Added `verify_release_controller_runtime_inputs`.
- Added `compose_release_controller_env`.
- Added `deploy_release_controller_image`.
- Added help text for `release-controller-image <image>`.
- Added main dispatch case for `release-controller-image`.

## Verification

- `bash -n deploy`
  - Passed.
- `./deploy | rg -n "services-image|factory-image|release-controller-image"`
  - Confirmed existing services/factory commands remain and new command is listed.
- `./deploy release-controller-image novaic/release-controller:latest`
  - Failed locally with mutable-tag rejection before remote sync/deploy.

## Known Gaps

- The command was not executed against the API host in this ticket. Remote deployment and smoke testing are assigned to P005.

## Artifacts

- `deploy`
