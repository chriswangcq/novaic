# Run focused projection cleanup verification

## Problem Definition

After test residue deletion and guard label cleanup, focused projection test suites must prove the desired contracts still hold across Cortex, runtime, and factory/log redaction.

## Proposed Solution

Run the focused Cortex projection tests, runtime projection/multimodal guard tests, and factory chat/log tests touched by the current projection work. Record failures as blocking follow-up if any occur.

## Acceptance Criteria

- Cortex projection tests pass.
- Runtime projection guard/multimodal tests pass.
- Factory chat/log tests pass.
- Any failure is recorded rather than ignored.

## Verification Plan

Run the explicit pytest commands and record exact outcomes.

## Risks

- Focused tests may miss unrelated full-suite failures, but they cover the projection cleanup scope.

## Assumptions

- Full repository test execution is outside this specific cleanup ticket unless focused tests expose broader breakage.
