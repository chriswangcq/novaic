# Repair Explicit Session Generation Fixtures

## Problem Definition

The targeted P608 Cortex/runtime projection verification fails two tests in `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py` because legacy test contexts omit the now-required explicit `session_generation`. The production contract correctly rejects missing generation, so the repair should update fixtures rather than weaken runtime validation.

## Proposed Solution

Inspect the failing tests and helper builders, then patch the narrowest fixture-level context dictionaries to pass an explicit positive `session_generation`. Keep production `session_generation` validation unchanged and avoid any fallback compatibility branch.

## Acceptance Criteria

- The two failed P608 tests pass.
- The full targeted P608 Cortex/runtime artifact projection test command passes cleanly.
- No production code path is loosened to allow missing `session_generation`.
- The test changes are minimal and local to the affected fixtures/helpers.

## Verification Plan

Run the two failed tests first, then re-run the full targeted P608 Cortex/runtime artifact projection command and capture output in the ledger tmp directory.

## Risks

- If the fixtures reflect an actual production path missing generation, a test-only patch would hide a real bug; inspect call sites before patching.
- Broad helper edits could accidentally change unrelated test meaning.

## Assumptions

- The current runtime contract intentionally requires positive `session_generation` for ReactThinkInput and ReactActionsInput.
- P608 image/artifact behavior does not require production code changes for this follow-up.
