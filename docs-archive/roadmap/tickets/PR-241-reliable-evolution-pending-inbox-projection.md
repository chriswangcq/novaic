# PR-241 Reliable Evolution FSM-05C Pending Inbox Projection Observe

Status: `[x]`

## Goal

Build an observe-only pending inbox projection from unconsumed
`input_received` events and compare it with the legacy `tq_pending_triggers`
row. This creates the cutover proof needed before `session_ended()` can use
the inbox as the restart source of truth.

## Phase Ledger

```text
Phase: FSM-05C Append-only inbox projection
Subject: pending input view derived from unconsumed input events
Old source of truth: tq_pending_triggers one-row merge
New source of truth: unconsumed input_received events plus input_consumed projection
Input events: input_received
Decision function: build pending projection from explicit event payloads
State transition: observe-only; no live state transition
Outbox effects: none
Observation events: pending_projection_observed
Generation/idempotency key: session generation from shadow state; idempotent per legacy pending trigger id or projection empty marker
Shadow drift metric: payload drift flag in pending_projection_observed
Cutover switch: none
Rollback path: revert observe code and tests
Legacy deletion condition: pending projection ordering/drift tests pass and later cutover ticket consumes inbox directly
Tests: PR-241 projection tests plus pending trigger regression tests
Docs/guards to update: ticket index and architecture implementation record
```

## Scope

- Runtime only: `novaic-agent-runtime`.
- Add a pure-ish projection builder that turns explicit unconsumed input event
  payloads into the pending view shape.
- Record `pending_projection_observed` events after pending buffering and after
  pending restart cleanup.
- Compare projected pending metadata with legacy pending metadata.
- Keep live restart source as `tq_pending_triggers`.

## Out Of Scope

- Do not read pending from projection in live code.
- Do not delete `tq_pending_triggers`.
- Do not change merge semantics yet.
- Do not add durable outbox publishing.

## Small Tickets

- [x] **FSM-05C-A Projection builder**: build pending view from explicit
  unconsumed input event dictionaries.
- [x] **FSM-05C-B Observe drift on buffer**: append a projection observation
  after non-attachable inputs are buffered.
- [x] **FSM-05C-C Observe empty after restart**: append a projection observation
  after `session_ended()` consumes pending input events.
- [x] **FSM-05C-D Tests**: prove projection matches legacy merged pending and
  becomes empty after restart.

## Implementation Files

- `novaic-agent-runtime/queue_service/session_repo.py`
- `novaic-agent-runtime/tests/test_pr241_pending_inbox_projection.py`

## Explicit Dependency Boundary Review

Required shape:

- Projection input must be explicit event dictionaries, not hidden DB reads.
- DB reads stay inside `SessionRepository`/ledger adapter boundaries.
- Drift observation must not change live routing.

## Legacy Cleanup Ledger

Keep these deliberately for now:

- Legacy pending row remains the live restart source.
- Projection drift is an observation payload, not a cutover guard.

Deletion criteria:

- Later FSM-05D/05E can switch restart to inbox only after projection drift is
  proven zero in tests and operational observation.

## Verification

- `pytest tests/test_pr241_pending_inbox_projection.py tests/test_pr240_input_consumption_observe.py tests/test_pr153_pending_inbox_metadata.py`
- `pytest`
- `git diff --check`

## Review Result

Pass. The projection builder consumes explicit unconsumed input event
dictionaries and mirrors legacy pending merge semantics, including preserving
all `message_ids` while letting latest non-message metadata win. The observe
event records both legacy and projected pending shapes plus a drift flag; live
restart still reads `tq_pending_triggers`.

## Rollback

Revert this PR. It only adds observe-only projection events and tests.
