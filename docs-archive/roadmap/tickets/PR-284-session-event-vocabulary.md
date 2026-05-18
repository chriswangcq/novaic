# PR-284 — Session Event Vocabulary

Status: Closed

## Goal

Replace ad hoc session event names with a durable event vocabulary so replay,
audit, and cleanup can distinguish input, decision, publication, observation,
and finalization events.

## Scope

- Introduce session event type constants or value objects.
- Stop adding new `shadow:*` event keys on active code paths.
- Keep existing historical rows readable.
- Add tests for event keys emitted by dispatch/finalize paths touched in this
  migration.

## Dependencies

- PR-283 state taxonomy.

## Risks

- Some tests assert exact event-key strings.
- Legacy rows may still contain `shadow:*`; cleanup must not break rebuild.

## Acceptance Criteria

- New session harness code references named event constants.
- Compatibility for older `shadow:*` rows is explicit and isolated.
- Tests cover the current emitted event names.

## Verification

- Targeted event vocabulary tests.
- Grep review for newly introduced raw event strings.

## Closure Notes

- Added `queue_service/session_events.py` with named `SessionEventType`,
  `SessionEventKeyPrefix`, `session_event_key`, and an explicit
  historical-key alias helper.
- Replaced ledger-owned event type strings and touched repository transition
  event names with the vocabulary.
- Current event keys now emit the `session:*` wire prefix. Historical
  `shadow:*` rows remain deduped through the isolated alias adapter so an
  upgrade cannot duplicate old events.
- Added `tests/test_pr284_session_event_vocabulary.py`.
- Verified with targeted event/ledger/FSM tests and full runtime suite.
