# Release fixed TURN discovery to prod and staging

## Problem Definition

Prod and staging still run API backend images without the new Gateway `/api/turn/credentials` endpoint. The API host secret has been repaired, but the fixed code path must be committed, built, deployed, and verified through the Release Controller.

## Proposed Solution

Commit the gateway/common/app changes and parent pointers, push them to `main`, build an immutable API backend image with the Release Controller path, deploy that image to staging and prod, then query the namespace Gateway loopback endpoints with trusted headers to confirm relay-capable ICE servers are returned.

## Acceptance Criteria

- Relevant subrepo commits are created and pushed.
- Parent repo records updated submodule pointers and ledger artifacts.
- Release Controller deploys an immutable API backend image containing the TURN endpoint to staging and prod.
- Prod and staging `/api/turn/credentials` return `ice_servers` with `turn:` or `turns:` URLs.
- The API host has `turn_secret` in `/opt/novaic/etc/secrets.json`, matching coturn.

## Verification Plan

Run focused unit/config/lint checks before commit. Use Release Controller or its CLI entrypoint for build/deploy. Verify remote container images, Gateway health, and direct loopback TURN endpoint responses after deployment.

## Risks

- The existing app TypeScript suite has an unrelated pre-existing failing test import.
- If Release Controller build includes parent submodule pointers, the parent commit must be made after subrepo commits.
- Prod Gateway will fail fast if `turn_secret` is missing or unreadable, so verify secrets before deploy.

## Assumptions

- The API host remains the deployment target for both staging and prod.
- Release Controller has the necessary credentials/config already installed from prior deployment work.
