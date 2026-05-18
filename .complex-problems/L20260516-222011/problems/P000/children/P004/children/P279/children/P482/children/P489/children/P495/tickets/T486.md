# Finalize ownership final verification ticket

## Problem Definition

P495 must skeptically verify that P489's finalize ownership cleanup is truly closed after the producer audit and strictness implementation. It should catch surviving finalize fallback terms, missing stack contract regressions, and tests that still assert old contract fields.

## Proposed Solution

Run final targeted guards over wake finalize producers, finalizer code, and focused tests. Run the focused finalize/session compatibility test suite. Classify any remaining hits and record whether they are non-blocking or require a follow-up.

## Acceptance Criteria

- Final guard artifact proves no actionable `stack_depth_at_finalize` / `stack_known_at_finalize` hits remain in P489-owned finalizer/producers/tests.
- Focused finalize/session/compensation tests pass together.
- Any retained compatibility-looking hit is explicitly classified.

## Verification Plan

Use `rg` and focused `pytest` over wake finalize, React producers, saga compensation, finalize ownership tests, and legacy cleanup tests. Save artifacts under `.complex-problems/L20260516-222011/tmp/p495/`.

## Risks

- Recovery-owned fallback terms may still appear and should not be incorrectly counted as P489 failure.

## Assumptions

- P491 owns recovery archive fallback cleanup.
