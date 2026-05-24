# Complex Problem Ledger

Ledger: L20260524-113035
Schema: v6
Root: P000 - Centered branch-driven release controller
Status: done
Updated: 2026-05-24T05:50:24+00:00

## Problem Tree
- [done] P000: Centered branch-driven release controller
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
  - [done] P019: Enable autonomous branch polling and managed staging release path
    - [done] P020: Add autonomous release-controller polling loop
    - [done] P021: Bootstrap API-host worktree and redeploy controller
      - [done] P023: Publish platform release source to main
    - [done] P022: Document and verify autonomous release operation
  - [done] P024: Make release-controller execute real staging releases
    - [done] P025: Deploy SSH-capable release-controller digest and rerun staging release

## Active

## Blocked

## Done
- [x] P000: Centered branch-driven release controller
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
- [x] P019: Enable autonomous branch polling and managed staging release path
- [x] P020: Add autonomous release-controller polling loop
- [x] P021: Bootstrap API-host worktree and redeploy controller
- [x] P022: Document and verify autonomous release operation
- [x] P023: Publish platform release source to main
- [x] P024: Make release-controller execute real staging releases
- [x] P025: Deploy SSH-capable release-controller digest and rerun staging release

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
- [done] T019: Autonomous branch polling and managed staging path -> P019 (split)
- [done] T020: Autonomous polling loop implementation -> P020 (one_go)
- [done] T021: Managed worktree and API-host redeploy -> P021 (one_go)
- [done] T022: Publish release platform source -> P023 (one_go)
- [done] T023: Autonomous release operation docs and final verification -> P022 (one_go)
- [done] T024: Release-controller execution-capable image -> P024 (one_go)
- [done] T025: Deploy fixed release-controller digest and verify staging release -> P025 (one_go)

## Latest Checks
- [success] C021: P020 P020 is successful. The service now has an explicit, test-covered autonomous polling loop that is disabled by default and visible through `/v1/status`.
- [success] C022: P023 P023 is successful. The platform release source is now committed and pushed on `main`, and the API-host worktree has fast-forwarded to the published commit with the required Docker/deploy release paths.
- [success] C023: P021 P021 is successful. The API-host worktree is now a release-capable git checkout, the updated release-controller image is deployed by digest, and autonomous polling is running in dry-run mode.
- [success] C024: P022 P022 is successful. The docs now match the deployed autonomous polling state and include concrete enable, pause, inspect, dry-run, and worktree repair operations.
- [success] C025: P019 P019 is successful. The release-controller now owns autonomous branch polling, the API host has a managed release worktree, and the deployed service is observing `main` in dry-run mode without GitHub Actions.
- [not_success] C026: P000 The controller now owns autonomous branch polling and observes `main -> staging` without GitHub Actions, but the root CI/CD goal is not fully successful yet. A hard execution check showed the release-controller container does not currently expose a usable `docker` or `docker compose` CLI, so non-dry-run build/publish/deploy execution is not proven.
- [not_success] C027: P024 Docker/Compose execution path works, but the fixed SSH-capable digest is not deployed and verified yet.
- [success] C028: P025 SSH-capable controller was deployed and a full non-dry-run main-to-staging release succeeded through smoke.
- [success] C029: P024 Release-controller now executes real staging releases end to end.
- [success] C030: P000 Centered branch-driven release-controller is implemented, deployed, and proven by a successful non-dry-run staging release.
