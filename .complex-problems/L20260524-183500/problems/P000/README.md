# Eliminate manual backend deploy paths behind Release Controller

## Problem

NovAIC backend and LLM Factory deployments currently still have direct operator-facing paths in `deploy` (`services-image`, `factory-image`, remote-build fallbacks, and legacy single-service deploys). The desired platform shape is that Release Controller is the only release interface for backend/factory namespaces, while `deploy` remains only an internal executor invoked by Release Controller with explicit run identity. Direct manual deployment paths should fail fast and documentation/tests should stop presenting them as valid release workflows.

## Success Criteria

- Release Controller deploy plans pass an explicit controller invocation identity into backend and Factory deploy steps.
- The command runner preserves the host environment while adding step-specific controller identity env vars.
- Direct manual execution of backend/factory image deploy paths fails before touching remote hosts.
- Remote-build and legacy backend deployment paths are removed from the normal operator surface or hard-fail as obsolete manual paths.
- Tests/guards cover controller env injection, env merging, and manual-path rejection.
- Documentation describes Release Controller API/polling/promotion/rollback as the only backend/factory deployment interface, with `deploy` documented as internal executor only.
- The change is safely rolled out so staging and prod releases continue to work through Release Controller, not manual scripts.
