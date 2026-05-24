# Build branch-driven release controller

## Problem Definition

NovAIC currently has a correct image-based deployment substrate, but long-term CI/CD is still conceptually tied to GitHub Actions. We need a self-owned centered release-controller that observes branches, builds and publishes immutable images, deploys namespace releases, records release state, supports promotion/rollback, and exposes operational status without making GitHub Actions the primary control plane.

## Proposed Solution

Create a `novaic-release-controller` service and Docker package. The controller will use a configured git remote and branch rules to poll commits, run verification commands, build API backend and LLM Factory images, push them to the API host registry, call the existing `./deploy services-image` and `./deploy factory-image` paths, and store release/run state under `/opt/novaic/release-controller`. It will expose a small HTTP API for status, manual trigger, promote, and rollback. The first deployment will run on the API host alongside the existing local registry and Docker socket.

## Acceptance Criteria

- A design document defines responsibilities, state model, branch rules, run lifecycle, failure behavior, promotion, rollback, and security boundaries.
- A controller implementation exists with deterministic config loading, branch polling, run locking, command execution, image publishing, deploy invocation, status API, and durable state.
- The controller is containerized with Compose and namespace-safe runtime directories.
- Tests/guards cover branch mapping, state persistence, command planning, immutable ref validation, and deploy safety constraints.
- The API host can run the controller in Docker and report health/status.
- Existing GitHub Actions docs are demoted to optional secondary path; controller is documented as the primary long-term path.
- Old local branches are reviewed and stale ones are deleted or archived after preserving current work.

## Verification Plan

Run unit tests and CI guards locally. Render Compose config. Run a dry-run release plan against the current git branch. Deploy the controller container on the API host, check `/health` and `/v1/status`, and verify it can see branch heads without triggering an unsafe prod release. Confirm branch cleanup with `git branch`.

## Risks

- Building images inside a controller container requires Docker socket access; the boundary must be explicit and limited to the release host.
- Automatic branch deployment can be dangerous if branch rules are ambiguous; prod must require explicit promotion command rather than automatic deploy from arbitrary branches.
- Current worktree is dirty; branch cleanup must not discard uncommitted work.
- Full end-to-end auto deploy may take long because image builds are heavy; dry-run and non-prod trigger verification should be available.

## Assumptions

- API host remains `root@api.gradievo.com`.
- Existing image deploy commands are the deployment authority.
- The API host local registry at `127.0.0.1:5000` can remain the internal registry until a separate registry decision is made.
- Nginx remains outside the controller.
