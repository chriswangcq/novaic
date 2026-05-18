# Classify Sandbox Mount Ownership and Bypass Residue

## Problem Definition

P629 must verify that mount/source_root/stable_cwd handling is owned by the correct layers: SDK DTOs describe requests, Cortex LogicalFS plans views, and sandbox-service performs service-internal mount namespace work. Client-side or runtime mount bypasses must not remain.

## Proposed Solution

Scan SDK/service/Cortex/runtime code for mount/source_root/stable_cwd/bind/namespace/host path terms, cite representative slices, classify ownership by layer, and run focused sandboxd/logicalfs/mount tests.

## Acceptance Criteria

- Exact scans and outputs are recorded.
- SDK mount hits are DTO-only or test fixtures.
- Cortex mount hits are LogicalFS planning only.
- Sandbox-service mount hits are service-internal namespace work.
- Runtime/client-side mount bypasses create a follow-up.
- Focused mount/logicalfs tests pass.

## Verification Plan

Run SDK tests, sandbox-service tests, and Cortex sandboxd/logicalfs mount tests.

## Risks

- Host path strings appear naturally in test fixtures and service mount validation.
- Runtime does not own mount planning; absence of runtime mount code is expected.

## Assumptions

- Base64/public-history was handled by P628.
