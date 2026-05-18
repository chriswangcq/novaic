# PR-194 — Entangled Schema Hardening Program

Status: `[implemented]`

## Goal

Make Entangled a hard schema/sync foundation instead of relying on upstream
services to notice soft failures. Schema registration must be validated,
atomic from the client's point of view, broadcast only after success, and
observable through readiness.

## Big Tickets

1. **PR-194A — Schema validator and SQL identifier guard**
   - Validate entity/table/field/default-order/key-param/id-field contracts in
     Entangled before any registry or database mutation.
   - Reject SQL reserved identifiers such as `order`.

2. **PR-194B — Atomic schema registration and safe broadcast**
   - Parse and validate the whole batch first.
   - Apply schema migrations as one batch.
   - Swap registry and broadcast only after the full batch succeeds.

3. **PR-194C — Entangled readiness contract**
   - Keep `/v1/health` as liveness.
   - Add readiness semantics for non-empty and required entity schemas.

4. **PR-194D — Business/Device schema push fail-fast**
   - Business and Device startup must fail if Entangled rejects schemas or
     registers fewer entities than expected.

5. **PR-194E — Runtime SQL boundary guardrails**
   - Validate runtime `order_by`, filter keys, CAS keys, and cleanup ordering
     against schema fields before SQL is built.

## Implementation Notes

- Entangled now validates schema batches before any DDL, registry mutation, or
  schema broadcast.
- Schema registration is all-or-nothing from the client contract: invalid
  batches return non-2xx and do not publish a partial registry.
- `/v1/health` remains liveness; `/v1/ready` reports schema readiness.
- Business and Device schema push now fail fast on response errors or registered
  entity mismatch.
- Runtime SQL field fragments are checked against registered schema fields.

## Validation

- `Entangled/packages/server-python`: `python3 -m pytest -q` → 61 passed.
- `novaic-business`: `python3 -m pytest -q` → 155 passed.
- `novaic-device`: `python3 -m pytest -q` → 8 passed.

## Execution Protocol

For every big ticket:

1. Analyze current state.
2. Create the small implementation checklist inside the ticket.
3. Implement against the checklist.
4. Run unit tests and smoke tests.
5. Close only when the ticket is actually收口; otherwise continue at step 3.
