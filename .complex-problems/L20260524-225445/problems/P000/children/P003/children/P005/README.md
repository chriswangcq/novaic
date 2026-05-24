# Make image release recover from corrupt staging Compose state

## Problem

The final WebRTC release cannot finish because Docker Compose left the `novaic-staging` project in a corrupt recreate state: half-created containers exist, some normal staging containers still point at the previous image, and even `docker compose ps -a` fails with `No such container`. The Release Controller path must be able to recover from this state without manual release scripts becoming the normal deployment path.

## Success Criteria

- The `services-image` deploy path has a clear namespace-scoped recovery step for Compose recreate corruption.
- Recovery only targets the requested namespace project, not unrelated prod or host infrastructure containers.
- The final parent commit is released to staging through Release Controller using immutable images.
- Staging smoke checks pass after recovery.
- Prod is promoted through Release Controller from the exact staging images that passed.
- The final prod/staging release pointers reference the final parent commit.
