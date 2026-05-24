# P015 Success Check

## Summary

P015 is successful. The deploy script now has an image-based `release-controller-image <image>` path that uses the existing immutable-ref guard style and leaves the existing `services-image` and `factory-image` paths intact.

## Evidence

- `deploy` help lists `release-controller-image <image>`.
- Existing `services-image` and `factory-image` commands remain in help and dispatch.
- `normalize_image_ref` supports `release-controller`.
- Mutable ref `novaic/release-controller:latest` is rejected locally before remote sync/deploy.
- `bash -n deploy` passed.

## Criteria Map

- Help lists command: satisfied.
- Mutable refs rejected: satisfied by local `latest` rejection.
- Existing commands preserved: satisfied by help output and dispatch entries.
- Shell syntax validation passes: satisfied by `bash -n deploy`.
- Local dry/help validation demonstrates reachability: satisfied.

## Execution Map

- Added release-controller deploy constants.
- Added compose package sync, env writing, runtime input verification, compose wrapper, and deploy command.
- Added help and dispatch entries.
- Ran local validation commands.

## Stress Test

- The mutable-tag rejection test proves the command fails before any remote side effects for a forbidden image ref.

## Residual Risk

- Remote execution of the new deploy command remains untested until P005 deploy verification.

## Result IDs

- R010
