# P517 Session Outbox Finalize Focused Tests Result

## Summary

Executed the session/outbox/finalize focused pytest subset. The run failed with 3 failures and 244 passes, so this ticket produced actionable failure evidence rather than a passing verification.

## Done

- Built the focused subset from the selected test list.
- Ran pytest from `novaic-agent-runtime`.
- Saved full pytest log.

## Verification

- Subset file count: `52`
- Pytest log: `.complex-problems/L20260516-222011/tmp/p517/session-outbox-finalize-pytest.log`
- Pytest summary: `3 failed, 244 passed in 1.29s`
- Failed tests:
  - `tests/test_pr233_active_inbox_dispatch.py::test_wake_finalize_failure_records_suspected_dead_event`
  - `tests/test_pr237_session_outbox_observe.py::test_outbox_records_start_and_published_attach_effects_after_cutover`
  - `tests/test_pr281_session_outbox_wrapper_boundary.py::test_session_repository_no_longer_owns_outbox_append_publish_helpers`

## Known Gaps

- Recovery archive now reports `remaining_stack.known == False` where the test expected `True`.
- Attach outbox observe test expects both effects `published`, but attach remains `pending`.
- Session repository wrapper-boundary test expects two `require_outbox=True` occurrences, but source now has one.
