# Build event projection read adapter

## Problem Definition

Phase 4 needs Cortex LLM context reads to stop depending on DFS over materialized `context.jsonl`, `steps/*.json`, and `summary.md`. The write path now appends ContextEvents and only keeps filesystem files as projection artifacts. The next read-path step is a small adapter that prepares LLM context from the event log and existing pure projection code, without touching the API handlers yet.

## Proposed Solution

Add an explicit event-projection read adapter inside `novaic_cortex` that:

- Reads the authoritative `ContextEventStore` stream for a root scope path.
- Projects events with the existing pure `project_context_events` function.
- Applies the existing budget compaction/token counting boundary to projected messages.
- Returns a prepared context object with compacted messages, projected active stack, estimated tokens, usage ratio, applied sequence, and a status view.
- Accepts all dependencies explicitly: workspace, root scope path, compact config, token counter, and optionally event store.
- Does not call `ContextEngine`, DFS context readers, or materialized step/summary files.

Keep the adapter narrow so later tickets can replace API `prepare_for_llm` and `status(include_usage=True)` without duplicating read logic in handlers.

## Acceptance Criteria

- A new adapter module exists and prepares messages only from `ContextEventStore` plus `project_context_events`.
- Adapter output exposes the same core data API handlers need: messages, stack, estimated tokens, usage ratio, applied sequence, and status.
- Unit tests cover notification projection, assistant tool-call/tool-result pairing, closed skill summary projection, and budget/token behavior through the adapter.
- Static scan proves the adapter does not import or call `ContextEngine` or materialized DFS read files.

## Verification Plan

- Run the new focused adapter tests.
- Run a static scan for forbidden adapter dependencies: `ContextEngine`, `context.jsonl`, `steps/*.json`, and `summary.md`.
- Run the full Cortex test suite after implementation if the focused tests pass.

## Risks

- Stack ordering may differ between the existing DFS helper and event projection. Keep the adapter’s stack semantics explicit and covered by tests.
- Budget compaction behavior can be brittle if tests depend on exact token counts. Test stable high-level behavior instead of fragile numeric internals.
- API cutover will happen in a later ticket, so this ticket must not leave duplicate handler logic.

## Assumptions

- `ContextEventStore.read_events(root_scope_path)` is the authoritative read boundary for Phase 4.
- `project_context_events` is already the pure projection boundary and can be reused directly.
- Existing `CompactConfig`, `budget_compact`, and token counter utilities remain the correct budget boundary for prepared LLM messages.
