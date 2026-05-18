# Check: Historical display replay coverage is direct

## Summary

Success. `R580` maps the historical display replay invariants to focused tests that would fail if history replay fetched Blob bytes or created image/user-image content.

## Evidence

- `R580` records scan and test artifacts:
  - `.complex-problems/L20260516-222011/tmp/p594/history-replay-scan.txt`
  - `.complex-problems/L20260516-222011/tmp/p594/history-replay-tests.txt`
- `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py:316-359` proves history projection does not resolve `image_ref` and does not fetch Blob bytes.
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py:340-462` proves mixed shell/display history/current ordering projects old shell as `history` and current display as `display_perception`.
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py:36-45` proves the history projection marker does not create user image content.

## Criteria Map

- Exact scans and focused tests recorded: satisfied.
- Tests proving historical display uses `history`: satisfied by PR71 and mixed replay tests.
- Tests proving image refs remain non-resolved: satisfied by the no-fetch assertion and retained `image_ref` payload check.
- Follow-up if missing: not needed.
- Belongs under P582 split: satisfied; this child covers history replay only.

## Execution Map

- `T586` executed a bounded read-only inventory and ran focused pytest.
- Focused command passed: `3 passed in 0.05s`.
- No code changes were needed.

## Stress Test

- Plausible failure mode: old display output contains a BlobRef and the runtime mistakenly fetches it as a fresh image in a later turn.
- Covered by `test_expand_messages_for_llm_does_not_resolve_history_image_ref`, where any Blob fetch raises an assertion and the expanded content remains `image_ref`.

## Residual Risk

- This child does not check durable shell/display output shape or active-stack ordering beyond the mixed replay test; sibling children cover those contracts.

## Result IDs

- R580
