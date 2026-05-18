# Attach generation final verification ticket

## Problem Definition

P498 must close the attach-generation branch under P490 by proving that inventory and hardening left no unclassified no-generation compatibility residue. It should produce final guard artifacts, run focused attach/session tests together, and classify any remaining compatibility-looking hits.

## Proposed Solution

Run the focused attach/session pytest suite used by P500 plus final `rg` guard sweeps over active runtime code and relevant tests. Save a final classification artifact that distinguishes production strict paths, test fixtures, and any remaining risk. If an unguarded compatibility path is found, do not hide it; record a not-success check with a follow-up.

## Acceptance Criteria

- Final guard artifact classifies remaining attach/generation hits.
- Focused attach/session tests pass together.
- Remaining compatibility-looking hits are explicitly classified as guarded test fixtures, strict production validation, or follow-up risk.

## Verification Plan

- Run focused pytest suite for attach/session generation paths.
- Run `rg` sweeps for optional generation contracts, direct `SESSION_ATTACH_INPUT` publication, `expected_wake_scope_id`, `expected_session_generation`, and `build_attach_input_effect`.
- Write a final classification Markdown artifact under `.complex-problems/L20260516-222011/tmp/p498/`.

## Risks

- Guard output can be noisy due to intentional test assertions.
- This verifies attach generation cleanup only; other P482 children remain separate.

## Assumptions

- P496 and P497 are already checked successful before P498 runs.
