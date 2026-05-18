# Ticket: Cortex Archive Diagnostics Persistence

## Problem Definition

P372 ensures runtime sends explicit archive diagnostics to Cortex, but Cortex still records generic archive semantics from active-stack projection. The explicit runtime diagnostics (`session_generation`, `finalize_reason`, `remaining_stack`, `round_num`) must become durable archive/context-event metadata where appropriate.

## Proposed Solution

Inspect Cortex `scope_end` and `_append_wake_archived_event` persistence flow. Add a narrow persistence contract that writes explicit runtime finalize diagnostics into the `WakeArchived` context event payload when diagnostics are present, while preserving existing semantic active-stack `remaining_stack` behavior for pure Cortex structural lifecycle tests. Ensure diagnostics are not synthesized from active lookup; they must come from the request contract validated by `ScopeEndRequest`.

## Acceptance Criteria

- Valid diagnostic `ScopeEndRequest` produces durable archive/context-event metadata containing explicit `session_generation`, `finalize_reason`, diagnostic `remaining_stack`, and `round_num`.
- Pure structural Cortex `scope_end` callers without diagnostics keep existing event payload semantics.
- Invalid/missing explicit generation cannot produce diagnostic archive metadata.
- No active-stack lookup is used to synthesize diagnostic generation.
- Focused Cortex tests prove diagnostic persistence and legacy-neutral structural behavior.

## Verification Plan

- Add or update focused Cortex scope-end tests around `WakeArchived` payloads.
- Run `python3 -m py_compile novaic_cortex/api.py`.
- Run focused Cortex context event lifecycle tests.

## Risks

- Cortex currently has a semantic `remaining_stack` list in `WakeArchived`. Runtime diagnostics use a different dict shape. The implementation must not conflate the two; it should either add a nested diagnostics object or clearly named diagnostic fields.

## Assumptions

- Runtime boundary propagation is complete under P372.
- Recovery/aggregate verification remains in sibling tickets after this persistence step.
