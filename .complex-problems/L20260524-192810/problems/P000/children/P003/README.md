# Roll out Release Controller quality gates on API host

## Problem

The new quality-gate capability only solves the operational problem after the API-host Release Controller is upgraded and its runtime config contains the gate list. The rollout must avoid the same old-controller/new-code race: pause polling, publish the code, deploy the upgraded controller, enable gates in remote config, run a controlled staging trigger or observe polling, then confirm failures would block before build/deploy.

## Success Criteria

- API-host polling is paused before pushing a controller change that requires the new gate model.
- Code and submodule pointers for the quality-gate change are committed and pushed intentionally.
- API-host Release Controller image is rebuilt/pushed/deployed from the quality-gate commit.
- Remote `/opt/novaic/release-controller/config.json` includes the intended quality gates.
- A staging run through Release Controller shows quality gate steps before image build/deploy and succeeds.
- Release Controller status is clean, polling is re-enabled, staging remains healthy, and prod pointer is not accidentally changed unless explicitly promoted.
