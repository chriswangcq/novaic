# Cut read paths from DFS source to ContextEvent projection

## Problem Definition

Phase 3 made ContextEvents the write artifact, but read paths still use `ContextEngine` DFS traversal over `context.jsonl`, `steps/_index.jsonl`, `steps/*.json`, `summary.md`, and `meta.json`. `prepare_for_llm`, usage/status diagnostics, and stack reads must move to event replay/projection semantics so files are no longer read as context source-of-truth.

## Proposed Solution

- Introduce an event-projection read adapter for API read paths:
  - read events from `ContextEventStore`,
  - project with `project_context_events`,
  - apply existing budget compaction,
  - return the existing prepared context contract.
- Cut `/v1/context/prepare_for_llm` to projection-first/no-DFS behavior.
- Cut `/v1/context/status(include_usage=True)` to projection usage estimates.
- Replace status stack authority where possible with projection stack, while preserving LIFO validation paths until fully event-backed.
- Add tests that cover active wake messages, notification hints, tool calls/results, nested skills, closed summaries, and stale sibling semantics from events.
- Keep DFS `ContextEngine` only as explicit legacy/projection debug support until final cleanup.

## Acceptance Criteria

- `prepare_for_llm` uses ContextEvent projection as the primary source.
- `context_status(include_usage=True)` does not instantiate DFS `ContextEngine`.
- Tests prove prepared messages match event semantics across active wake, closed summaries, nested skills, tools, and notifications.
- DFS file traversal is not silently used as fallback when event projection fails.
- Full Cortex suite passes.

## Verification Plan

- Add focused projection/API prepare tests.
- Static scan `api.py` for `ContextEngine` usage in prepare/status paths.
- Run full Cortex suite.

## Risks

- Existing DFS-rendering tests are numerous and represent legacy projection behavior; they may need to be split from API read-path cutover.
- Event projection may not yet implement every DFS rendering edge case; gaps should be split into follow-up child problems, not hidden behind fallback.

## Assumptions

- No historical migration is required; old pre-event data can be reset.
- Workspace projection files may still exist for debug/shell, but API prompt context should use events.
