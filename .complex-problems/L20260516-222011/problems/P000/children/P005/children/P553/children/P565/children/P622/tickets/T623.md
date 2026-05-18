# Classify Sandbox Wire Base64 and Mount Residue

## Problem Definition

P622 must classify base64 and mount-related residue across sandbox SDK/service/Cortex integration so private wire encoding and intended mount DTOs are not confused with public LLM history leakage or host mount bypasses.

## Proposed Solution

Run exact scans over `novaic-sandbox-sdk`, `novaic-sandbox-service`, and Cortex sandbox/logicalfs/shell code for base64/stdout_b64/stderr_b64/mount/source_root/stable_cwd/host path terms; cite relevant slices; classify each surface; run focused wire/mount tests.

## Acceptance Criteria

- Exact scan commands and outputs are recorded.
- Wire base64 encode/decode is classified as private or risky public leakage.
- Mount fields and mount namespace helpers are classified as DTO, service-internal, or risky bypass.
- Focused SDK/service/Cortex tests pass.
- Any public base64 leak or client-side mount bypass creates a follow-up.

## Verification Plan

Run SDK tests, sandbox-service tests, and Cortex sandboxd/logicalfs/shell projection tests.

## Risks

- Base64 appears in tests and wire contracts by design.
- Mount appears in DTOs, LogicalFS planning, and service mount namespace internals; classification must respect ownership layers.

## Assumptions

- P620 and P621 closed service/client boundaries but P622 performs a cross-cutting residue pass.
