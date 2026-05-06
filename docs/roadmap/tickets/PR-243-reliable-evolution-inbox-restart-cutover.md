# PR-243 Reliable Evolution FSM-05E Inbox Restart Cutover

Status: `[x]`

## Goal

Cut `SessionRepository.session_ended()` restart source from the legacy
`tq_pending_triggers` row to the pending projection derived from unconsumed
`input_received` events.

## Phase Ledger

```text
Phase: FSM-05E inbox restart cutover
Subject: session_ended restart source
Old source of truth: tq_pending_triggers
New source of truth: unconsumed input_received projection
Input events: input_received
Decision function: pending projection builder
State transition: no_active -> restarted when projection exists; no_active -> closed otherwise
Outbox effects: existing observe-only create_wake_saga effect
Observation events: pending_projection_observed, input_consumed, session_restarted/session_closed
Generation/idempotency key: new wake scope id/session generation from injected providers
Shadow drift metric: pending_projection_observed.drift
Cutover switch: none; direct code cutover
Rollback path: revert PR-243
Legacy deletion condition: after PR-243 passes, PR-244 can remove pending writes/reads
Tests: restart works after legacy pending row is removed; stale legacy row no longer restarts
Docs/guards to update: ticket index and architecture implementation record
```

## Scope

- Runtime only: `novaic-agent-runtime`.
- Build restart input from the pending inbox projection.
- Continue deleting legacy pending rows during session cleanup so old state does
  not accumulate.
- Keep dispatch pending writes until the follow-up removal ticket.
- Preserve merged metadata semantics and message id ordering.

## Out Of Scope

- Do not delete `tq_pending_triggers` table/write path yet.
- Do not change active attach behavior.
- Do not change watchdog/recovery semantics.
- Do not introduce outbox publishing.

## Small Tickets

- [x] **FSM-05E-A Projection restart source**: convert pending projection into
  the restart saga input shape.
- [x] **FSM-05E-B Cut `session_ended()` source**: restart/closed decision uses
  projection, not legacy pending row.
- [x] **FSM-05E-C Legacy row cleanup**: continue deleting old pending rows during
  cleanup but do not treat them as source of truth.
- [x] **FSM-05E-D Tests**: prove restart works without legacy pending row and
  stale legacy pending alone does not restart.

## Implementation Files

- `novaic-agent-runtime/queue_service/session_repo.py`
- `novaic-agent-runtime/tests/test_pr243_inbox_restart_cutover.py`

## Explicit Dependency Boundary Review

Required shape:

- Restart source is explicit event payload snapshots plus projection builder.
- DB reads stay inside repository/ledger boundaries.
- Clock/id values remain injected providers.

## Legacy Cleanup Ledger

Keep these deliberately for now:

- Dispatch still writes `tq_pending_triggers` for one more cleanup ticket.
- `list_pending_triggers()` remains diagnostic.

Deletion criteria:

- PR-244 removes pending writes/reads and updates guardrails once PR-243 is
  green.

## Verification

- `pytest tests/test_pr243_inbox_restart_cutover.py tests/test_pr242_strict_input_ledger.py tests/test_pr241_pending_inbox_projection.py tests/test_pr153_pending_trigger_metadata.py tests/test_pr233_active_inbox_dispatch.py`
- `pytest`
- `git diff --check`

## Review Result

Closed.

- `session_ended()` now derives restart source from unconsumed
  `input_received` projection.
- Legacy `tq_pending_triggers` row is still deleted during session cleanup but
  no longer controls restart/close.
- Tests prove restart works after the legacy pending row is removed, and a stale
  legacy row without inbox input closes the session instead of restarting.
  The stale-row case records `pending_projection_observed.drift=true`.

## Rollback

Revert this PR to restore `session_ended()` legacy pending source.
