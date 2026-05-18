# Audit Sandbox Service Execution Boundary Residue

## Problem Definition

P620 must audit `novaic-sandbox-service` for active execution bypasses, local fallback execution, host path exposure, mount bypasses, and stale compatibility routes that could undermine sandboxd as the process execution service.

## Proposed Solution

Run static scans over service code/tests, cite relevant execution/mount/base64 slices, classify hits, and run focused service tests.

## Acceptance Criteria

- Service scan and slices are recorded.
- Fallback/local/host/mount/base64 hits are classified.
- Focused service tests pass.
- A follow-up is created if active service code bypasses sandboxd or exposes unsafe host paths.

## Verification Plan

Run `pytest novaic-sandbox-service/tests` or the focused subset if the full suite is too broad.

## Risks

- Test fixtures may intentionally include host paths and fallback words; classify source vs test.

## Assumptions

- Service-internal process execution is the service boundary; the risk is bypassing service from clients or unsafe host path exposure, not service doing its own execution.
