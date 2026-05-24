# Complex Problem Ledger

Ledger: L20260524-113035
Schema: v6
Root: P000 - Centered branch-driven release controller
Status: doing
Updated: 2026-05-24T04:55:04+00:00

## Problem Tree
- [followup] P000: Centered branch-driven release controller
  - [done] P001: Release-controller discovery and architecture design
  - [done] P002: Implement release-controller core service
    - [done] P007: Release-controller config and model foundation
    - [done] P008: Release-controller persistent state store
    - [done] P009: Release-controller branch planner and command runner
    - [done] P010: Release-controller HTTP control plane
    - [done] P011: Release-controller core unit tests
    - [done] P012: Add release-controller branch head polling
  - [done] P003: Containerize and integrate release-controller deployment
    - [done] P013: Package release-controller Docker image
    - [done] P014: Integrate release-controller into Compose runtime
    - [done] P015: Add release-controller deploy script path
  - [done] P004: Add release-controller tests and CI guards
  - [done] P005: Deploy release-controller to API host and verify
  - [done] P006: Migrate CI/CD docs and clean stale branches
    - [done] P016: Update release-controller CI/CD docs
    - [done] P017: Inspect and clean stale local branches
  - [done] P018: Wire deployed release-controller branch polling
  - [followup] P019: Enable autonomous branch polling and managed staging release path
    - [done] P020: Add autonomous release-controller polling loop
    - [doing] P021: Bootstrap API-host worktree and redeploy controller
      - [doing] P023: Publish platform release source to main
    - [todo] P022: Document and verify autonomous release operation

## Active
- [ ] P000: Centered branch-driven release controller (followup)
- [ ] P019: Enable autonomous branch polling and managed staging release path (followup)
- [ ] P021: Bootstrap API-host worktree and redeploy controller (doing)
- [ ] P022: Document and verify autonomous release operation (todo)
- [ ] P023: Publish platform release source to main (doing)

## Blocked

## Done
- [x] P001: Release-controller discovery and architecture design
- [x] P002: Implement release-controller core service
- [x] P003: Containerize and integrate release-controller deployment
- [x] P004: Add release-controller tests and CI guards
- [x] P005: Deploy release-controller to API host and verify
- [x] P006: Migrate CI/CD docs and clean stale branches
- [x] P007: Release-controller config and model foundation
- [x] P008: Release-controller persistent state store
- [x] P009: Release-controller branch planner and command runner
- [x] P010: Release-controller HTTP control plane
- [x] P011: Release-controller core unit tests
- [x] P012: Add release-controller branch head polling
- [x] P013: Package release-controller Docker image
- [x] P014: Integrate release-controller into Compose runtime
- [x] P015: Add release-controller deploy script path
- [x] P016: Update release-controller CI/CD docs
- [x] P017: Inspect and clean stale local branches
- [x] P018: Wire deployed release-controller branch polling
- [x] P020: Add autonomous release-controller polling loop

## Tickets
- [done] T000: Build branch-driven release controller -> P000 (split)
- [done] T001: Discover and design release-controller architecture -> P001 (one_go)
- [done] T002: Implement release-controller core service -> P002 (split)
- [done] T003: Build release-controller config and model foundation -> P007 (one_go)
- [done] T004: Implement release-controller persistent state store -> P008 (one_go)
- [done] T005: Implement release-controller planner and command runner -> P009 (one_go)
- [done] T006: Implement release-controller HTTP control plane -> P010 (one_go)
- [done] T007: Verify release-controller core unit tests -> P011 (one_go)
- [done] T008: Implement release-controller branch head polling -> P012 (one_go)
- [done] T009: Containerize and integrate release-controller deployment -> P003 (split)
- [done] T010: Package release-controller Docker image -> P013 (one_go)
- [done] T011: Integrate release-controller into Compose runtime -> P014 (one_go)
- [done] T012: Add release-controller image deploy command -> P015 (one_go)
- [done] T013: Add release-controller tests and CI guards -> P004 (one_go)
- [done] T014: Deploy release-controller to API host and verify -> P005 (one_go)
- [done] T015: Migrate release-controller CI/CD docs and clean stale branches -> P006 (split)
- [done] T016: Update release-controller CI/CD docs -> P016 (one_go)
- [done] T017: Inspect and clean stale local branches -> P017 (one_go)
- [done] T018: Wire deployed release-controller branch polling -> P018 (one_go)
- [splitting] T019: Autonomous branch polling and managed staging path -> P019 (split)
- [done] T020: Autonomous polling loop implementation -> P020 (one_go)
- [executing] T021: Managed worktree and API-host redeploy -> P021 (one_go)
- [executing] T022: Publish release platform source -> P023 (one_go)

## Latest Checks
- [success] C012: P003 P003 is successful. The release-controller now has Docker image packaging, Compose runtime integration, and an image-based deploy command path. Actual host rollout remains correctly assigned to P005.
- [success] C013: P004 P004 is successful. The release-controller has repository-level guards that run through root pytest and protect the core tests, Dockerfile, Compose runtime, and deploy entrypoint invariants without requiring Docker daemon access.
- [success] C014: P005 P005 is successful. The release-controller is running on the API host as a Docker Compose service, bound only to loopback, using the immutable digest image ref, and verified through health/status and dry-run trigger checks.
- [success] C015: P016 P016 is successful. Documentation now reflects the deployed release-controller path, the operator commands, loopback-only exposure, GitHub Actions fallback role, and the remaining managed-worktree limitation.
- [success] C016: P017 P017 is successful. Local stale branches were cleaned while preserving unmerged branch tips under archive refs, and the current branch remains `main`.
- [success] C017: P006 P006 is successful. The docs now describe the deployed self-hosted release-controller path and local stale branches have been cleaned safely with archive refs for unmerged tips.
- [not_success] C018: P000 The release-controller work is substantially complete but not fully successful against the centered branch-driven goal. The deployed service can run manual dry-run triggers and the codebase includes a poller module, but the deployed HTTP service does not yet expose or run branch polling, and the API host worktree is not yet a managed checkout for real non-dry-run branch releases.
- [success] C019: P018 P018 is successful. The deployed release-controller now exposes a branch polling control-plane path, the API host can call it successfully in dry-run mode, and the worktree requirement is documented with an explicit bootstrap command.
- [not_success] C020: P000 The release-controller is deployed and can poll branch heads through its control-plane API, but the root problem is not fully successful yet. The remaining gap is autonomy: the service should own periodic branch polling and the API host should have the managed worktree needed for non-dry-run staging releases.
- [success] C021: P020 P020 is successful. The service now has an explicit, test-covered autonomous polling loop that is disabled by default and visible through `/v1/status`.
