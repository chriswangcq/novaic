# Implement Active Stack Projection Helper

## Problem Definition

Operational SQLite can store active stack frames, but there is no small boundary module that normalizes top-first frames, writes the projection, and optionally records a durable control event with explicit reason/idempotency. Runtime wiring should depend on that helper instead of duplicating frame shape rules.

## Proposed Solution

Add a `novaic_cortex.active_stack_projection` module with explicit pure-ish helpers:

- Normalize active-stack frames into stable top-first dictionaries.
- Reject malformed frames before writing.
- Write `active_stack_projection` through `OperationalSqliteStore.set_active_stack`.
- Optionally append a stack projection event to `scope_events` with explicit reason and idempotency key.
- Return structured projection/event details for runtime callers and tests.

## Acceptance Criteria

- Helper requires explicit `operational_store`, `root_scope_id`, `frames`, `generation`, and `reason`.
- Frame normalization is deterministic and keeps only stable fields.
- Empty stack writes `top_scope_id=None`.
- Nested top-first stack writes preserve top scope and frame order.
- Unit tests cover empty, nested, malformed, and idempotent event cases.

## Verification Plan

- Add targeted tests for the helper.
- Run helper tests and operational-store tests.
- Run `py_compile` on the new helper and store module.

## Risks

- If the helper accepts arbitrary frame data, later API responses may drift. Keep the field set intentionally small.
- Appending an event and setting projection are separate store calls unless the store grows a compound operation; tests should still catch idempotent retry behavior.

## Assumptions

- Runtime API wiring happens in P023/P024, not this helper ticket.
