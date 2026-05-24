# Add release-controller image deploy command

## Problem Definition

The release-controller has Docker and Compose packaging, but the top-level `deploy` entrypoint does not yet know how to deploy a controller image. Operators need a clear image-based path that preserves the existing services/factory deployment behavior.

## Proposed Solution

Extend `deploy` with a `release-controller-image <image-ref>` command that:

- rejects mutable refs unless explicitly local
- syncs or verifies runtime files on the API host
- writes/uses a release-controller environment file
- runs the release-controller Compose project with the provided image ref
- preserves existing `services-image` and `factory-image` commands

Keep the new path narrow and visible in help text.

## Acceptance Criteria

- `deploy` help lists the release-controller image command.
- Mutable refs are rejected by the same immutable-ref policy used for other image deployments.
- Existing services/factory image commands are not removed or renamed.
- Shell syntax validation passes.
- A local dry/help validation demonstrates the new command is reachable.

## Verification Plan

- Inspect current `deploy` image deployment functions.
- Patch `deploy` using existing patterns.
- Run `bash -n deploy`.
- Run help/usage output check.
- Run relevant deploy guard checks if present.

## Risks

- Breaking the existing deployed services-image/factory-image paths would be high-impact.
- The command must not rebuild on the host.

## Assumptions

- Actual remote deployment and smoke testing are handled by P005.
