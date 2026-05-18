# Fix Runtime Projection Session Generation Test Fixtures

## Problem

The P608 artifact/image rendering audit found that the targeted Cortex/runtime projection test suite is not fully clean because two legacy tests in `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py` construct React saga contexts without the required explicit `session_generation`. This blocks P608 closure even though the artifact/image projection behavior itself appears mostly sound.

## Success Criteria

- Update the minimal outdated test fixtures or helper builders so the tests use explicit positive `session_generation` values that match the current runtime contract.
- Re-run the targeted Cortex/runtime artifact projection tests and record a clean pass.
- Confirm the fix does not loosen production generation requirements and does not add compatibility fallback code for missing generation.
