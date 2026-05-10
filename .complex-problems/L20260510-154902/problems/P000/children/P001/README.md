# Phase 0: Event-sourced context design and construction plan

## Problem

Write the final design document and construction plan for the full Cortex event-sourced context source model. The document must define source events, stream identity, ordering, idempotency, projections, old-data deletion policy, and cutover invariants before implementation begins.

## Success Criteria

- A repo design document exists with final architecture, event schema, projection model, and migration/no-compat policy.
- The document names exact current paths to delete or demote from source-of-truth to projection.
- The document defines implementation phases and strict checks for each phase.
- The design avoids permanent dual truth and explains how old data reset works.
