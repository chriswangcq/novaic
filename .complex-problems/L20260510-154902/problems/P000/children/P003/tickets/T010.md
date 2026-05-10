# Implement ContextEvent projections and replay

## Problem Definition

The ContextEvent substrate can store ordered events, but there is not yet a pure replay/projector that derives LLM context state, active stack, folded skill summaries, tool result placement, notification hints, and projection metadata from the event stream. Without this, later read-path cutover would either keep legacy DFS traversal or duplicate projection logic in endpoints.

## Proposed Solution

- Add a pure projection module independent of Workspace IO.
- Define projection input as ordered `ContextEvent` objects and output as a deterministic snapshot with:
  - `root_scope_id`;
  - `applied_seq`;
  - `messages`;
  - `stack`;
  - optional `estimated_tokens`/metadata.
- Implement replay for:
  - root/wake start/archive;
  - system prompt/message append;
  - input notification hints;
  - skill scope open/close with LIFO validation;
  - assistant tool call and tool step events.
- Preserve Phase 0 projection semantics:
  - closed non-empty skills fold to `[Skill '<name>' completed]\n<report>`;
  - blank structural closed scopes can expose child folds;
  - newest unanchored open sibling suppresses stale open siblings;
  - tool results attach by `call_id`;
  - notification hints do not fetch user message bodies.
- Add tests for simple messages, notification hints, fold behavior, nested skill scopes, stale open sibling suppression, tool call/result placement, archive/final stack, and applied sequence.

## Acceptance Criteria

- A pure ContextEvent projector exists and can be tested without Workspace IO.
- Projection output includes messages, active stack, root id, and applied sequence.
- Projection handles all Phase 0 event classes needed for LLM context semantics.
- Tests cover fold behavior, nested skills, stale open sibling suppression, tool result placement, and notification hint semantics.
- No current endpoint/read path is cut over in this phase.

## Verification Plan

- Run focused projection tests.
- Run existing event substrate tests.
- Run relevant existing ContextEngine tests to ensure no regression.
- Static search/diff review for accidental endpoint cutover.

## Risks

- Projection semantics can become too large if copied from DFS engine all at once; split pure state replay from rendering behavior.
- Tool-result placement is easy to under-specify; tests must anchor call_id behavior.
- If projection fetches IM bodies or workspace files, it violates the event-source model.

## Assumptions

- Events arrive ordered by `seq`; store/order validation is handled by Phase 1.
- Budget compaction remains out of scope for Phase 2 unless needed for snapshot shape.
