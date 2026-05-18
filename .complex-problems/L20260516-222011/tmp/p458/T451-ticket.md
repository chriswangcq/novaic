# Ticket: Map session outbox effect inventory

## Problem Definition

Map the session outbox effect model end to end: effect types, payload identity fields, recording points, worker delivery, and downstream handler boundaries.

## Proposed Solution

- Inspect `queue_service/session_outbox*`, `session_repo`, `session_effects`, `session_wake_plan`, `session_observed_events`, and task/runtime handlers.
- Use focused `rg` guards for outbox/effect/publish/create/record/deliver names.
- Save raw guard outputs under `.complex-problems/L20260516-222011/tmp/p458/`.
- Produce a concise effect inventory table with file references.

## Acceptance Criteria

- Every session outbox effect type is listed.
- Recording and delivery paths are mapped.
- Downstream handler boundaries are named.
- Unknown effect or unmapped path becomes a follow-up or sibling target.

## Verification Plan

- Cross-check source guard outputs against the final inventory table.
- Do not modify source files in this inventory ticket.
