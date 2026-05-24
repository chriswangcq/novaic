# Complex Problem Ledger

Ledger: L20260524-183500
Schema: v6
Root: P000 - Eliminate manual backend deploy paths behind Release Controller
Status: done
Updated: 2026-05-24T11:09:39+00:00

## Problem Tree
- [done] P000: Eliminate manual backend deploy paths behind Release Controller
  - [done] P001: Enforce Release Controller-only backend deploy entrypoints in code
  - [done] P002: Roll out controller-only deployment and clean release documentation
    - [done] P003: Validate and publish controller-only release commit
    - [done] P004: Upgrade remote Release Controller and verify controller-only deployment

## Active

## Blocked

## Done
- [x] P000: Eliminate manual backend deploy paths behind Release Controller
- [x] P001: Enforce Release Controller-only backend deploy entrypoints in code
- [x] P002: Roll out controller-only deployment and clean release documentation
- [x] P003: Validate and publish controller-only release commit
- [x] P004: Upgrade remote Release Controller and verify controller-only deployment

## Tickets
- [done] T000: Make backend releases controller-only -> P000 (split)
- [done] T001: Add controller invocation contract and deploy guards -> P001 (one_go)
- [done] T002: Roll out guarded deploy through Release Controller -> P002 (split)
- [done] T003: Validate, pause polling, commit and push -> P003 (one_go)
- [done] T004: Upgrade controller and run guarded staging/prod verification -> P004 (one_go)

## Latest Checks
- [success] C000: P001 P001 is solved at the code/guard layer. The implementation now provides a Release Controller invocation contract, preserves runner environment, rejects direct manual backend/factory image deploys, disables obsolete backend/factory manual targets, and has focused tests/lints for those rules. Rollout is deliberately outside this child and remains open under P002.
- [success] C001: P003 P003 is complete for the Release Controller migration path: the controller/deploy preflight is green, polling was paused before push, only intended files were committed, and parent plus submodule commits were pushed to `main`. The full monorepo matrix remains a separate historical test debt and is not part of the controller runtime preflight configured on the API host.
- [success] C002: P004 P004 is successful. The API host is now running a Release Controller image built from the controller-only commit, staging and prod were deployed via Release Controller runs, manual backend/factory deploy entrypoints reject direct use before remote mutation, and health/status verification shows clean release state with polling enabled.
- [success] C003: P002 P002 is successful. The rollout order avoided the old-controller/new-guard race, backend and Factory releases now execute through Release Controller, docs and CI guards no longer present direct deploy/GitHub Actions as backend release paths, and manual executor calls are rejected without controller identity.
- [success] C004: P000 P000 is successful within its stated backend/Factory release scope. Release Controller is now the only backend/factory release interface; direct executor paths fail without controller identity; obsolete backend remote-build and legacy targets are disabled; tests, docs, guards, staging, prod promotion, health, polling, and rollback dry-run all support the new shape.
