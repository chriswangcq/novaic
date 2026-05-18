# PR-194E — Entangled Runtime SQL Boundary Guardrails

Status: `[implemented]`

## Current-State Analysis

Entangled validates values through parameters, but several SQL structural
fragments (`order_by`, filter keys, CAS keys, cleanup ordering) are constructed
from caller-provided field names. Those should be restricted to schema fields.

## Small Tickets

- [x] Reuse the schema validator's field/order helpers at runtime.
- [x] Guard `list`, `list_stream`, `count`, `delete_where`, `update_where`,
      `cleanup`, and `cas_update`.
- [x] Add tests showing SQL fragment injection is rejected.
- [x] Confirm normal Business/Device order/filter usage still works.

## Validation

- Entangled SQL guard tests.
- Existing Entangled CRUD/sync tests: 61 passed.
