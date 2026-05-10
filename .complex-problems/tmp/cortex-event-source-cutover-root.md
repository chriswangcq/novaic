# Cortex full event-sourced context source cutover

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
