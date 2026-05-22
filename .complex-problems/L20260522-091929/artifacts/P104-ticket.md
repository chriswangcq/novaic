# Validate Queue Migration Timestamp Binding

## Problem Definition

The migration copy path deliberately passes ISO timestamp strings through to the Postgres adapter for TIMESTAMPTZ binding, but tests currently assert JSON conversion more strongly than timestamp preservation. P104 needs to make timestamp behavior explicit and covered.

## Proposed Solution

1. Extend `tests/test_queue_migration_copy.py` success assertions to cover representative timestamp columns already present in fixture data.
2. Assert timestamp preservation across:
   - task projection/event/state/outbox;
   - saga projection/state;
   - worker lease event/state/outbox;
   - idempotency ledger;
   - session event/state/outbox.
3. Add a small code comment or test assertion wording documenting that ISO timestamp strings are deliberately passed through for Postgres TIMESTAMPTZ binding.
4. No production code change unless the test exposes a real conversion gap.

## Acceptance Criteria

- Representative timestamp columns are explicitly asserted in target-bound rows.
- Tests document pass-through timestamp binding behavior.
- Existing migration planner/copy/validation/CLI tests still pass.

## Verification Plan

- Update `tests/test_queue_migration_copy.py`.
- Run all migration tests plus Queue Postgres boundary and compile checks.

## Risks

- Over-normalizing timestamps could alter production data; prefer preserving source values unless evidence says otherwise.

## Assumptions

- SQLite source timestamp strings are already ISO-style Queue timestamps accepted by Postgres TIMESTAMPTZ binding.
