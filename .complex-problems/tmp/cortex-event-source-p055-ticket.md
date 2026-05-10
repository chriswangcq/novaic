# Cut prepare_for_llm API to event projection

## Problem Definition

`/v1/context/prepare_for_llm` still imports and runs the DFS `ContextEngine`, so LLM request assembly can still depend on materialized context/step artifacts even though the write path is now event-first. This ticket cuts the primary LLM prepare endpoint to the new event read adapter.

## Proposed Solution

Update `context_prepare_for_llm` to:

- Load the same engine/compact config boundary it uses today.
- Instantiate `ContextEventReadModel` with workspace, root scope path, and compact config.
- Return `CortexPreparedContext` from the adapter’s prepared messages, top-first stack, and estimated token count.
- Remove the render/control drift comparison from this endpoint because both messages and stack now come from one event projection source.
- Do not keep a DFS fallback path.

Keep `context_status(include_usage=True)` and broader DFS cleanup for the next tickets, so this ticket is limited to the primary prepare endpoint.

## Acceptance Criteria

- `context_prepare_for_llm` no longer imports or instantiates `ContextEngine`.
- The endpoint uses `ContextEventReadModel` as the only context assembly source.
- Endpoint behavior is covered by API tests that prove prepared messages include event-projected notifications/tool results/summaries.
- Static scan confirms `ContextEngine` no longer appears in the prepare endpoint.

## Verification Plan

- Run focused context event API prepare/read tests.
- Run static scan around `context_prepare_for_llm` for `ContextEngine` and old drift helpers.
- Run full Cortex tests.

## Risks

- Existing tests may assume DFS materialized artifacts are visible through prepare. Those should be migrated to event expectations, not preserved with compatibility fallback.
- Stack order must remain API-compatible: current top first.

## Assumptions

- `ContextEventReadModel` from P054 is the intended read boundary.
- `load_engine_config` and `engine_config_to_compact_config` remain the budget config source for this ticket.
