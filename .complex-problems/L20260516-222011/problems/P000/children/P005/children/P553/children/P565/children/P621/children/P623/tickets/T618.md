# Audit Sandbox SDK API and Wire Boundary

## Problem Definition

P623 must determine whether `novaic-sandbox-sdk` has any active local execution, fallback, host path/mount manipulation, or public byte/base64 leakage that violates the sandboxd service boundary.

## Proposed Solution

Scan SDK production and test code for execution/session API, subprocess/process/local/fallback/host/mount/base64/stdout/stderr/compat terms, inspect relevant slices, classify hits, and run focused SDK tests if present.

## Acceptance Criteria

- Exact scan commands and outputs are recorded.
- SDK public API and wire handling slices are cited.
- Every hit is classified as intended wire/client code, test fixture, risky fallback, or removable residue.
- Focused SDK tests pass or missing coverage is explicitly recorded.
- Any active local execution/fallback or public byte leakage creates a follow-up.

## Verification Plan

Run focused `novaic-sandbox-sdk` tests and, if no dedicated test suite exists, inspect package/test inventory and record the gap.

## Risks

- SDK must decode service wire payloads; base64 hits are not automatically bugs.
- Test fixtures may contain host paths or encoded strings.

## Assumptions

- Sandbox service internals are out of scope here and covered by P620.
