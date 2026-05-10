# Add sandboxd process-boundary guardrails

## Problem Definition

P001 showed sandboxd currently looks process-only, but there is no residue test
that prevents future code from adding Cortex Workspace, Blob, or live `RO` / `RW`
semantics into sandbox-service.

## Proposed Solution

Add focused boundary tests for sandbox-service:

- sandbox-service must not import Cortex, Blob Service, or LogicalFS business
  adapters.
- sandbox-service package source must not contain workspace/scope/subagent/blob
  authority terms except generic process/mount contract language.
- existing sandbox-service execution tests must still pass.

## Acceptance Criteria

- Guard tests fail if sandbox-service imports Cortex or Blob modules.
- Guard tests fail on obvious Cortex workspace/Blob ownership vocabulary in
  sandbox-service source.
- Existing sandbox-service tests pass.
- Deployment scripts continue to reference sandbox-service as a process service.

## Verification Plan

Run sandbox-service tests plus focused residue scans over sandbox-service and
deployment scripts.

## Risks

- Guard terms must avoid false positives for generic mount contract names.

## Assumptions

- Sandbox SDK may contain mount contracts but not Cortex workspace semantics.
