# PR-297 — Session Event Alias Removal

Status: Closed

## Goal

Remove historical `shadow:*` session event idempotency alias handling so the
session ledger has one current event-key vocabulary only.

## Scope

- Delete historical event key prefix helpers from runtime code.
- Make `SessionLedgerRepository.append_event()` dedupe only on the provided
  current idempotency key.
- Replace alias compatibility tests with current-prefix guard tests.
- Update residue checks so `shadow:*` cannot re-enter active session code.

## Dependencies

- PR-284 session event vocabulary.
- PR-294 legacy residue cleanup.

## Risks

- Existing databases with old `shadow:*` keys will no longer dedupe against
  current keys. This is accepted because this no-backcompat cleanup deliberately
  drops old data compatibility.

## Acceptance Criteria

- No runtime code contains `historical_session_event_keys` or
  `HISTORICAL_SESSION_EVENT_KEY_PREFIX`.
- Session event vocabulary tests assert current `session:*` keys only.
- Runtime tests pass.

## Verification

- Grep for historical alias helpers.
- Targeted session event vocabulary tests.
- Full runtime test suite.

## Closure Notes

- Removed `HISTORICAL_SESSION_EVENT_KEY_PREFIX` and
  `historical_session_event_keys()` from `session_events.py`.
- `SessionLedgerRepository.append_event()` now dedupes only on the exact current
  idempotency key supplied by the caller.
- Replaced the historical `shadow:*` alias test with a current `session:*`
  idempotency guard.
- Verified by targeted PR-284 test and full runtime suite:
  `pytest` in `novaic-agent-runtime` -> 364 passed.
