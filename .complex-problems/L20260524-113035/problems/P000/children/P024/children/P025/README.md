# Deploy SSH-capable release-controller digest and rerun staging release

## Problem

`P024` proved that the release-controller can run the real Docker/Compose build and push path, but the deployed controller image failed at `deploy-api-staging` because `ssh` was missing. Source and image changes now include `openssh-client`, `rsync`, and a read-only SSH directory mount. The fixed digest must be deployed and exercised.

## Success Criteria

- The API host runs release-controller image digest `127.0.0.1:5000/novaic/release-controller@sha256:8bd2205a8a2b4cc21c7101f4d70ac06f410e36f5ea9837375c7ab5ff7cf7b0aa` or a newer immutable digest containing the same SSH/runtime fix.
- Inside the running controller container:
  - `docker --version` works.
  - `docker compose version` works.
  - `ssh` exists and can run in batch mode against the deploy target.
  - `rsync` exists.
  - The host Docker socket is accessible.
- A non-dry-run `main -> staging` trigger reruns the real release path.
- Staging API and LLM Factory health checks pass after the run, or the next exact runtime blocker is recorded with command output.
- Prod remains promotion-only.

## Initial Action

Deploy the fixed digest through `./deploy release-controller-image ...`, restart/recreate the controller if Compose does not replace the container, then run the container capability checks and a non-dry-run trigger.
