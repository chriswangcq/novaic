# Upgrade API-host controller and verify quality gates execute

## Problem

After the quality-gate commit is pushed, the running API-host controller must be upgraded to an image built from that commit and the remote runtime config must include `quality_gates`. A staging run must prove the gates execute before build/deploy and block semantics remain controller-owned.

## Success Criteria

- A new Release Controller image is built/pushed/deployed from the quality-gate commit.
- Remote `/opt/novaic/release-controller/config.json` contains the intended `quality_gates` and preserves existing registry, branch, health, and polling settings.
- A staging run through Release Controller succeeds with command plan order: git/submodule, `quality-*`, preflight, build, push, deploy, smoke.
- Staging public health is clean after the run.
- Prod current pointer remains unchanged unless deliberately promoted.
- Polling is re-enabled and Release Controller status has `last_error=null`.
- Manual direct backend/factory deploy commands still fail locally before remote side effects.
