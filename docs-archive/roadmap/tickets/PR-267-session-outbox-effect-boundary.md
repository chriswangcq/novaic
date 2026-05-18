# PR-267 Session Outbox Effect Boundary

Status: Closed

## Goal

Move create-wake and attach-input durable outbox effect payload construction out
of `SessionRepository` into deterministic pure helpers.

## Scope

- Add `queue_service.session_effects`.
- Preserve current effect shapes and idempotency keys.
- Keep effect type constants injected from `SessionRepository`.
- Keep agent root scope derivation explicit at the repository boundary.
- Remove repository-private effect builder helpers.

## Out Of Scope

- Publishing behavior and retry policy remain unchanged.
- Recovery archive effect shaping was handled in PR-266.

## Small Tickets

- [x] **FSM-267-A Pure effect helpers**: add create-wake and attach-input
  builders.
- [x] **FSM-267-B Repository cutover**: call pure builders from dispatch and
  restart paths.
- [x] **FSM-267-C Tests/residue**: pin effect shapes and remove old helper
  references.
- [x] **FSM-267-D Explicit attach boundary**: pass attach effect fields
  explicitly instead of forwarding `**attach_request` and ignoring surplus
  `saga_id`.
- [x] **FSM-267-E Verification**: run outbox targeted tests and full runtime
  tests.

## Verification

- `pytest tests/test_pr267_session_outbox_effect_boundary.py tests/test_pr248_attach_outbox_cutover.py tests/test_pr251_wake_creation_outbox_cutover.py tests/test_pr233_active_inbox_dispatch.py`
- Full runtime `pytest`.

## Review Result

Pass. Create-wake and attach-input durable outbox effect payloads now live in
`queue_service.session_effects`. `SessionRepository` no longer owns those payload
shapes and keeps only append/publish boundary logic. Attach effect construction
now receives an explicit field list; no unused `saga_id` compatibility sink or
`**attach_request` forwarding remains.
