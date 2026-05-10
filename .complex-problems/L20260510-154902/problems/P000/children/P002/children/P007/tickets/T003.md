# Define ContextEvent schema module

## Problem Definition

P007 needs a deterministic ContextEvent schema/validation layer before any storage or integration is written. Current context code is DFS-oriented (`ContextEngine`, `StepTreeBuilder`, `Workspace` step/context files), so the schema must stand on its own and avoid hidden IO/time/id dependencies.

## Proposed Solution

- Add a new focused module under `novaic-cortex/novaic_cortex/` for ContextEvent domain types and validation.
- Define constants for schema version and allowed event types from the Phase 0 design document.
- Represent the ContextEvent envelope as a typed dataclass with explicit fields and `to_dict` / `from_dict` helpers.
- Add validation and canonical semantic-body helpers:
  - require non-empty `event_id`, `stream_id`, `root_scope_id`, `occurred_at`, `actor`, and valid `type`;
  - require positive integer `seq`;
  - require object/dict `payload`;
  - reject stream/root mismatch where applicable;
  - produce deterministic JSON/canonical body for idempotency comparison while excluding generated fields.
- Add unit tests for valid construction, malformed events, canonical equality, deterministic serialization, and allowed event type coverage.

## Acceptance Criteria

- ContextEvent schema and validation code exists and is independent from Workspace IO.
- The allowed event type list covers Phase 0 target event types.
- Invalid envelopes produce clear typed errors rather than generic crashes.
- Canonical semantic body comparison is stable and deterministic.
- Focused tests pass.

## Verification Plan

- Run the new focused tests.
- Run static search to confirm the new domain module does not call `time`, `uuid`, `os.environ`, or workspace/filesystem APIs.
- Review diff to ensure P007 only introduces schema/validation and tests, not storage or endpoint cutover.

## Risks

- Over-modeling can make later phases heavy; keep the schema strict but small.
- Under-modeling event types now can force ad hoc later changes.
- If canonical body includes generated fields, idempotency will be flaky.

## Assumptions

- Phase 0 design is the source for event type names and envelope fields.
- Storage append/read is handled by P008/P009, not this ticket.
