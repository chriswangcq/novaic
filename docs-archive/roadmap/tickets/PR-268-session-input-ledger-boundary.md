# PR-268 — Session Input Ledger Boundary

Status: Closed

## Goal

Move input inbox event accounting (`input_received` and `input_consumed`) behind `SessionLedgerRepository` so the Queue session coordinator and outbox dispatcher no longer hand-build session input ledger payloads.

## Why

The reliable session harness is migrating toward a generic FSM substrate with a small imperative shell. Input inbox events are ledger facts, not business branching decisions. Keeping their payload shape in `SessionRepository` or `SessionOutboxDispatcher` leaves a misleading second owner for the same event contract.

## Scope

- Add explicit `SessionLedgerRepository` methods for input received and input consumed facts.
- Keep generation, idempotency, payload shape, and consumed marker semantics in the ledger adapter.
- Update `SessionRepository` and `SessionOutboxDispatcher` to delegate input event accounting.
- Add tests that pin payload shape, idempotency, consumption marking, and source-residue removal.

## Non-Goals

- Do not redesign dispatch routing in this ticket.
- Do not alter outbox publication semantics beyond using the new ledger boundary.
- Do not add compatibility branches.

## Acceptance Criteria

- `SessionRepository` no longer constructs `event_type="input_received"` or `event_type="input_consumed"` payloads.
- `SessionOutboxDispatcher` no longer constructs `event_type="input_consumed"` payloads.
- Ledger tests prove deterministic input event payloads from explicit arguments.
- Existing append-only inbox, input consumption, attach outbox, and wake creation tests pass.
- Full `novaic-agent-runtime` test suite passes.

## Verification

- `pytest tests/test_pr268_session_input_ledger_boundary.py tests/test_pr239_append_only_inbox.py tests/test_pr240_input_consumption.py tests/test_pr153_pending_inbox_metadata.py tests/test_pr248_attach_outbox_cutover.py tests/test_pr251_wake_creation_outbox_cutover.py`
- `pytest`
- `git diff --check`

## Closure Notes

- Added `SessionLedgerRepository.append_input_received()` and `record_input_consumed()`.
- Updated `SessionRepository` and `SessionOutboxDispatcher` to delegate input ledger payloads to the ledger adapter.
- Updated strict boundary fake in `test_pr242_strict_input_ledger.py`.
- Added PR-268 tests for explicit payload shape, idempotency, consumed markers, and source-residue guards.
- Verified targeted suite: 21 passed.
- Verified full runtime suite: 304 passed.
- Verified `git diff --check`: clean.
