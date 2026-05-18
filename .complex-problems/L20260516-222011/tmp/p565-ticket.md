# Inventory Sandbox Service SDK Compatibility Residue

## Problem Definition

P565 must find sandbox service/core/SDK compatibility branches, host path exposure, mount bypasses, legacy execution paths, and stdout/stderr base64 handling that could bypass sandboxd or leak bytes into LLM history.

## Proposed Solution

Split into sandbox service boundary, sandbox SDK/client boundary, and wire/base64/mount residue classification. Each child records exact scans and tests, then parent aggregates.

## Acceptance Criteria

- Service/core/SDK scans are recorded.
- Compatibility/path/mount/base64 hits are classified.
- Sandboxd remains the execution service boundary; no direct legacy executor bypass remains reachable.
- Stdout/stderr base64 is classified as sandbox wire encoding, not public LLM history.

## Verification Plan

Run sandbox service and SDK focused tests plus any runtime shell integration tests that assert output contract.

## Risks

- Direct path strings can be legitimate test fixtures or internal mount specs; classify reachability before changing.

## Assumptions

- Local fallback execution paths are not desired unless explicitly in tests/mocks.
