# Deploy reasoning streaming through Release Controller CI/CD

## Problem

The reasoning streaming changes are implemented locally across `novaic-llm-factory`, `novaic-agent-runtime`, and `novaic-app`, but they are not yet published. The user wants the complete CI/CD deployment flow, using Release Controller rather than manual deployment scripts, until publication succeeds; at minimum the server-side release must be deployed and health-verified.

## Success Criteria

- Construction changes are committed in all touched subrepos and the root repo records the updated submodule pointers and ledger state.
- Code is pushed to the canonical remote branch used by the Release Controller.
- Release Controller is triggered through its supported API/control plane, not by direct manual deployment script execution.
- The server-side deployment reaches a successful published state in at least staging, and prod if the configured CI/CD policy supports immediate promotion for this request.
- Server-side health/smoke checks pass after deployment.
- Any failures are diagnosed, fixed or retried through the controller, and recorded with evidence.

## Notes

The current intended release path is centralized Release Controller. Manual deploy scripts are implementation details for the controller executor and should not be used directly as the deployment path.
