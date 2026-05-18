# T454 Result: Observed wake outbox residue cleanup

## Summary

Found real observed-wake outbox residue. Production source still defines `SessionOutboxDispatcher.OBSERVE_CREATE_WAKE_SAGA = "observe_create_wake_saga"` even though the supported effect set excludes it and observed wake-created is handled directly under `create_wake_saga` delivery. This should not be accepted as complete cleanup.

## Evidence

- Guard output: `.complex-problems/L20260516-222011/tmp/p462/observe-wake-before.txt`
- Production hit:
  - `novaic-agent-runtime/queue_service/session_outbox.py:30`
- Test hits:
  - `novaic-agent-runtime/tests/test_pr251_wake_creation_outbox_cutover.py:133`
  - `novaic-agent-runtime/tests/test_pr249_observed_wake_outbox_cleanup.py:148`
  - `novaic-agent-runtime/tests/test_pr249_observed_wake_outbox_cleanup.py:159`
  - `novaic-agent-runtime/tests/test_pr250_observed_wake_effect_rename.py:75`
  - `novaic-agent-runtime/tests/test_pr250_observed_wake_effect_rename.py:102`

## Classification

- Production constant: removable residue unless a repair ticket proves it is needed.
- Test references: likely negative guard tests and should be updated to assert literal removed effect behavior or no emitted row without relying on a production constant.

## Changes

No source changes were made in this execution attempt. The result records the gap so the check can create a concrete repair follow-up.

## Required Follow-up

Remove production `OBSERVE_CREATE_WAKE_SAGA` residue and update focused tests so they continue guarding against reintroduced observed-wake outbox effects without importing an obsolete production constant.
