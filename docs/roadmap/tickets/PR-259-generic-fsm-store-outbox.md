# PR-259 Generic FSM Store And Outbox

Status: Closed

## Goal

Extract the durable event/state/effect repository behind a generic FSM store
interface while preserving the existing session table data and behavior.

## Scope

- Add a generic store adapter for event append, state upsert/load, outbox append,
  pending outbox listing, publish ack, and failure accounting.
- Keep all time/ID providers injected at the repository boundary.
- Validate configured SQL identifiers at the generic substrate boundary; table
  and column names must be infrastructure config, not dynamic business input.
- Make `SessionLedgerRepository` a thin session adapter or delete it if the
  generic store can fully cover current callers.

## Cleanup Checklist

- [x] Delete duplicate session-only row conversion helpers if generic store owns
  JSON encoding/decoding.
- [x] Keep session-specific outbox effect constants only in the publisher; move
  status/publish accounting into the generic store.
- [x] Add residue scans for accidental direct table manipulation in
  `SessionLedgerRepository`.
- [x] Reject invalid table/column identifiers in `FsmSqliteStoreConfig` and row
  mutation helpers.

## Verification

- `pytest tests/test_pr259_generic_fsm_store_outbox.py tests/test_pr235_session_ledger.py tests/test_pr237_session_outbox_observe.py tests/test_pr251_wake_creation_outbox_cutover.py tests/test_pr257_remove_active_sessions_table.py`

## Review Result

Pass. `SessionLedgerRepository` is now a thin session identity adapter over
`FsmSqliteStore`; SQL insert/update/select mechanics and JSON encode/decode are
no longer duplicated in session-specific code. Existing session ledger/outbox
contracts still pass. The generic store also rejects dynamic SQL identifiers so
future consumers cannot accidentally turn infrastructure config into business
input.
