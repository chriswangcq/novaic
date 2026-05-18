# ContextEvent store and writer contract audit ticket

## Problem Definition

ContextEvent store/writer/model code is the append boundary for event-sourced context. It must have explicit clock/id/identity inputs and must not carry compatibility defaults that make event replay non-deterministic.

## Proposed Solution

Inspect `context_event_store.py`, `context_event_writer.py`, and `context_events.py`; run focused tests; patch only if a hidden default, implicit dependency, idempotency weakness, or malformed event compatibility branch is found.

## Acceptance Criteria

- Store, writer, and model files are inspected.
- Append identity, idempotency, clock, and id provider behavior are classified.
- Dangerous hidden defaulting or compatibility branches are removed if found.
- Focused store/writer/model tests pass.
- Any unresolved gap is split into a follow-up child.

## Verification Plan

- Read source slices directly.
- Run focused tests:
  - `tests/test_context_event_store.py`
  - `tests/test_context_event_writer.py`
  - `tests/test_context_event_model.py`
  - `tests/test_context_event_write_authority.py`

## Risks

- Event replay/idempotency bugs can be subtle; check both code and tests rather than relying on grep.

## Assumptions

- No source edit is needed if the explicit boundary is already clean and tested.
