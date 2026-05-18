# Normalize runtime generation default boundaries

## Problem Definition

Runtime still has widened-guard hits where generation-like control-plane values are coerced with raw `int(... or 0)`. Some are live session semantics, some are persistence adapters, and some are audit/projection counters. They must be separated and either fixed or explicitly classified.

## Proposed Solution

Split the work by boundary: pure session FSM finalize inputs, session repo/ledger state adapters, and audit/generic FSM classifications. For live session generation semantics, introduce or reuse explicit validators. For safe audit/projection/generic counters, document why they are not stale-session authority and add focused tests if the classification is non-obvious.

## Acceptance Criteria

- Session finalize FSM no longer silently coerces malformed `finalize_generation`.
- Session repo state reconstruction no longer silently defaults active generation in authority paths.
- Session ledger/audit/generic FSM hits are either patched or classified as safe non-session-authority adapters.
- Focused tests cover changed live boundaries.
- Narrow and widened guards produce a final classified matrix with no unclassified session generation residue.

## Verification Plan

Run focused session FSM/repo tests, affected generic FSM tests if touched, compile checks, and rerun both narrow and widened `rg` guards.

## Risks

- Some raw `int(... or 0)` patterns are legitimate counters or audit defaults; over-patching them could add ceremony without improving correctness.
- Session FSM is pure logic, so stricter validation must preserve existing valid finalize behavior.

## Assumptions

- No compatibility is required for malformed bool/missing generation in live session authority paths.
