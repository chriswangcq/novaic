# Materialized context owner classification result

## Summary

Classified all materialized context projection hits. The remaining live uses are legitimate but poorly named: they maintain `context.jsonl` projection / notification hint idempotency, not authoritative LLM prepare history. Cleanup is routed to P443/P444/P445.

## Done

- Saved focused scans for direct calls, endpoint strings, bridge helpers, and test/mock member usage.
- Saved source slices for runtime session init, runtime context read/append handlers, Cortex workspace projection helpers, and Cortex projection endpoints.
- Classified the live owners:
  1. **Runtime session-init projection seed**: `runtime_handlers.py` writes initial system prompt/context with `bridge.append_context_batch(...)`.
  2. **Runtime notification hint idempotency**: `context_handlers.py` reads materialized context to avoid double-appending environment notification hints, then appends missing hints.
  3. **Runtime assistant/system projection append**: `context_handlers.py` appends assistant/system messages to the materialized projection and activity timeline.
  4. **Cortex projection endpoints**: `/v1/context/read|append|batch` update/read `context.jsonl` projection while also appending ContextEvent message events for append/batch.
  5. **Cortex workspace projection helpers**: `read_context`, `append_context`, `append_context_projection`, `append_context_batch_projection` are materialized projection helpers.
  6. **Tests**: runtime context read/order/by-id tests and Cortex context event API tests cover projection behavior; prepare-path tests prove this projection does not feed LLM history.

## Verification

- Evidence artifacts:
  - `.complex-problems/L20260516-222011/tmp/p442/materialized-context-hits.txt`
  - `.complex-problems/L20260516-222011/tmp/p442/materialized-context-member-hits.txt`
  - `.complex-problems/L20260516-222011/tmp/p442/runtime-session-init-context-batch-slice.txt`
  - `.complex-problems/L20260516-222011/tmp/p442/context-read-handler-slice.txt`
  - `.complex-problems/L20260516-222011/tmp/p442/context-append-handler-slice.txt`
  - `.complex-problems/L20260516-222011/tmp/p442/workspace-materialized-context-slice.txt`
  - `.complex-problems/L20260516-222011/tmp/p442/api-materialized-context-slice.txt`

## Known Gaps

- P443 should narrow or rename runtime bridge helpers so projection-only APIs are not mistaken for LLM history APIs.
- P444 should make runtime context handler contracts explicit around notification/projection maintenance.
- P445 should clean Cortex endpoint/test naming and stale comments around materialized projection.

## Artifacts

- No source code changed in this classification ticket.
