# Runtime bridge focused test fixture result

## Summary

Fixed the stale runtime bridge focused test fixture by passing explicit positive `session_generation` to the React actions context. Production validation remains strict.

## Done

- Updated `novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py::test_tool_result_step_preserves_tool_call_id_and_step_ref`.
- Added `"session_generation": 1` to the fixture context.
- Reran the P437 focused runtime bridge suite.

## Verification

```text
36 passed in 0.22s
```

Artifact: `.complex-problems/L20260516-222011/tmp/p441/runtime-bridge-focused-pytest.with-status.txt`

## Known Gaps

None for this test-fixture cleanup.

## Artifacts

- `novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py`
- `.complex-problems/L20260516-222011/tmp/p441/runtime-bridge-focused-pytest.with-status.txt`
