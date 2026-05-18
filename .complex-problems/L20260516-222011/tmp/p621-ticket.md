# Audit Sandbox SDK Client Boundary Residue

## Problem Definition

P621 must audit `novaic-sandbox-sdk` and active runtime shell call sites to verify that clients use the sandboxd/service boundary rather than direct process execution, host path manipulation, local fallback, or public wire payload leakage.

## Proposed Solution

Run static scans over SDK production code/tests and runtime call sites, cite relevant source slices for client/session/exec APIs, classify fallback/local/host/base64 hits, and run focused SDK/runtime shell-output tests. If any active runtime path bypasses sandboxd, split a remediation follow-up instead of closing the problem.

## Acceptance Criteria

- Exact scan commands and outputs are saved under the ledger tmp directory.
- SDK/client behavior is classified as intended, risky, removable, or follow-up.
- Runtime shell call sites are verified to call the SDK/service boundary instead of direct legacy execution.
- Base64 handling is classified as private wire decoding or risky public history leakage.
- Focused SDK/runtime tests pass, or failures are recorded with a follow-up.

## Verification Plan

Run focused `novaic-sandbox-sdk` tests plus runtime shell output/tool handler tests that exercise the SDK boundary and terminal-output contract.

## Risks

- Tests may contain direct process or host path terms as fixtures.
- SDK may legitimately decode service wire base64 internally; the risk is exposing bytes to public history or offering a local fallback path.
- Runtime call sites may be split across queue/task modules and need exact citation.

## Assumptions

- `novaic-sandbox-service` internals were already classified by P620.
- Client code should treat sandboxd as the execution authority.
