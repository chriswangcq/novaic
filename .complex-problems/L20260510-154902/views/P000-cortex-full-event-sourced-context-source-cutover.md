# P000: Cortex full event-sourced context source cutover

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Replace Cortex LLM context source of truth with a complete event-sourced context source model. Old historical data may be deleted; no backward compatibility with pre-cutover workspace history is required. The work must include design documentation, construction plan, staged implementation, old-path cleanup, and strict verification.

## Success Criteria
- A design document defines the final event-sourced context model, event schema, projections, ownership boundaries, failure/replay semantics, and no-compat cutover rules.
- The work is split into explicit child problems; this root problem is not treated as a single one-go change.
- Context source facts are represented as append-only events with explicit ordering, idempotency, generation/versioning, and tenant/root scope identity.
- LLM context preparation reads from event-source/projection semantics instead of treating legacy DFS files as the source of truth.
- Existing legacy direct-source assumptions are deleted or clearly demoted to projections; no misleading half-migration path remains.
- Tests cover event append, replay/projection, skill begin/end, tool step, notification hint, active stack, stale open sibling, and LLM prepare behavior.
- Full relevant test suite passes and residual risks are explicitly documented.

## Subproblems
- P001: Phase 0: Event-sourced context design and construction plan
- P002: Phase 1: Context event store substrate
- P003: Phase 2: Context projections and replay
- P004: Phase 3: Write-path cutover to context events
- P005: Phase 4: Prepare/read-path cutover from events
- P006: Phase 5: Legacy cleanup, reset behavior, and full verification

## Results
- R062

## Latest Check
C066

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R062: problems/P000/results/R062.md
- Check C066: problems/P000/checks/C066.md

## Follow-ups
- none
