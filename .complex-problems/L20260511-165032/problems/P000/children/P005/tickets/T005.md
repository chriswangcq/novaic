# Audit Deployment and Compatibility Residue

## Problem Definition

Audit whether deployment and process wiring still expose old services, old fallback flags, or compatibility paths that bypass the new LogicalFS/Sandbox/FSM architecture.

## Proposed Solution

Inspect deployment scripts, startup scripts, process mode declarations, service status, and repository residue. Separate harmless historical docs/tests from deployable old runtime components.

## Acceptance Criteria

- Confirm current deploy/start scripts use the intended services.
- Identify old services or fallback components that are still deployable or started.
- Check whether compatibility cleanup steps exist for retired components.
- Record concrete file and command evidence.

## Verification Plan

- Inspect deployment/start scripts and backend mode declarations.
- Search for retired component names and fallback flags.
- Query current deployment status if available locally.

## Risks

- Some historical documentation and tests may mention retired components; those should not be confused with active deployment wiring.

## Assumptions

- A deploy residue is critical only if it can be started by current scripts or reached by current service configuration.
