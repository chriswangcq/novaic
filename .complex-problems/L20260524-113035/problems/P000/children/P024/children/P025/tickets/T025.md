# Deploy fixed release-controller digest and verify staging release

## Problem Definition

The release-controller source and image now include Docker CLI, Docker Compose, SSH, rsync, Docker socket access, and a read-only SSH directory mount, but the latest fixed digest has not yet been deployed and verified. The prior non-dry-run run reached the real deploy step and failed because `ssh` was not present.

## Proposed Solution

- Deploy immutable digest `127.0.0.1:5000/novaic/release-controller@sha256:8bd2205a8a2b4cc21c7101f4d70ac06f410e36f5ea9837375c7ab5ff7cf7b0aa` to the API host using `./deploy release-controller-image`.
- Force a restart/recreate if Compose does not replace the running container.
- Verify inside the running controller container:
  - Docker CLI.
  - Docker Compose plugin.
  - SSH client.
  - rsync.
  - Docker socket access.
- Trigger a non-dry-run `main -> staging` release.
- Verify staging API and staging LLM Factory health after the run.
- Keep production branch-trigger disabled; production remains promotion-only.

## Acceptance Criteria

- The API host is running the fixed release-controller digest or a newer immutable digest with the same executor dependencies.
- The running container passes Docker, Compose, SSH, rsync, and Docker socket checks.
- A non-dry-run `main -> staging` release either succeeds through deploy/smoke or records the next precise runtime blocker after the SSH step.
- Staging health is checked after the run.
- Production is not branch-triggered.

## Verification Plan

- `./deploy release-controller-image <digest>`
- API-host container capability checks with `docker exec`.
- `POST /v1/triggers` with `dry_run=false` for `main` and the current commit.
- API-host local health checks:
  - `http://127.0.0.1:29999/api/health`
  - `http://127.0.0.1:29990/health`
- Release-controller `/v1/status` confirms polling remains enabled and prod is not part of branch triggers.

## Risks

- Staging service deployment may expose a later missing secret, runtime dependency, or health issue. That is acceptable only if the failing command and output are captured precisely.
