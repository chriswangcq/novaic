# Cortex context event lifecycle cleanup ticket

## Problem Definition

ContextEvent lifecycle code is the semantic source for LLM context assembly. It must not carry hidden generation defaults, old active-state lookup behavior, or inline payload compatibility that can bypass the event-source model.

## Proposed Solution

Use the P416 live-surface map to audit and clean context event lifecycle code in focused slices:

1. ContextEvent store and writer append contracts.
2. ContextEvent projection/read-model behavior.
3. Workspace step/payload normalization where ContextEvents point to tool payloads.
4. Context assembly/API lifecycle endpoints that append or prepare context events.

Patch only dangerous live behavior. Classify legitimate projection metadata explicitly. Add or update focused tests for changed boundaries.

## Acceptance Criteria

- Every P416 context event lifecycle live file is inspected.
- No ContextEvent append/write path accepts hidden generation or stale active-state compatibility.
- Tool payload references stay pointer-oriented; inline result payload compatibility is rejected or externalized explicitly.
- Legitimate projection/read-model fields are classified and covered by tests.
- Focused Cortex context event tests pass.

## Verification Plan

- Inspect `context_event_store.py`, `context_event_writer.py`, `context_events.py`, `context_event_projection.py`, `context_event_read_model.py`, and related workspace step/payload normalization.
- Run focused Cortex tests around context event store/writer/projection/read model/API writes.
- Rerun a targeted context-event guard after cleanup.

## Risks

- Context event code is broad enough to hide multiple concerns; split further if store/writer/projection/workspace concerns cannot be closed together.
- Projection fields may look like compatibility but be legitimate read-model state.

## Assumptions

- Backward compatibility for old inline tool result payloads is not required.
- Event-source context is the intended authority; file projections are only materialized views.
