# PR-294A — Race Attach Event Vocabulary Cleanup

Status: Closed

## Goal

Delete retired race-attach/race-buffer event vocabulary after queued-start
state prevents duplicate wake starts before activation.

## Scope

- Remove unused race attach/race buffer event enum values.
- Remove unused race idempotency-key prefixes.
- Update residue tests so they guard absence of the retired active path.

## Dependencies

- PR-286B2A.
- PR-286D.

## Acceptance Criteria

- No active code or tests reference race attach/race buffer event names.
- Session harness tests pass.

## Verification

- Residue grep.
- Full runtime suite.

## Closure Notes

- Removed retired race attach/race buffer event enum values from
  `queue_service/session_events.py`.
- Removed unused race idempotency-key prefixes.
- Updated attach flow residue tests to assert the race attach consume path stays
  absent.
- Verified by targeted residue/vocabulary tests:
  `pytest tests/test_pr271_session_attach_flow_consolidation.py tests/test_pr273_session_harness_final_residue_guard.py tests/test_pr284_session_event_vocabulary.py tests/test_pr255_legacy_compat_cleanup.py`
  -> 14 passed.
