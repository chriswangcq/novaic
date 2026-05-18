# Context assembly source map and event boundary result

## Summary

Closed the full context assembly source-map split. The active path is now mapped from ContextEvent stream and workspace materializations through runtime prepare-context, tool step refs/payload refs, and active stack injection. The core contract is: ContextEvents/operational projections are the semantic source for LLM context, workspace files are materialized observability/retrieval surfaces, `step_ref` is stable lookup identity, `payload_ref` is actual storage identity, and active stack injection is transient common-assembly guidance.

## Done

- P133 mapped the ContextEvent append-only store, pure projection, and read-model/budget boundary.
- P134 mapped workspace materialized projections, step indexes, payload store, and blob externalization.
- P135 mapped runtime prepare-context saga/handler/LLM handoff and removed or classified local continuity residue.
- P136 mapped tool-result `step_ref`/`payload_ref` semantics from runtime wrapper through Cortex formatted read.
- P137 mapped active skill stack projection, final injection ordering, current display-media regression behavior, and stale injection cleanup.

## Verification

- Child success checks:
  - P133: C137
  - P134: C156
  - P135: C174
  - P136: C179
  - P137: C184
- Representative focused suites from the children:
  - ContextEvent and workspace suites from P133/P134.
  - Runtime prepare-context suite from P135: `47 passed in 0.22s`.
  - Tool-result ref contract suites from P136: Cortex `80 passed`, runtime `62 passed`.
  - Active stack injection suites from P137: source/order/display/cleanup slices all passed.

## Known Gaps

- No active correctness gap remains in the mapped context assembly path.
- Separate future cleanup can consider broader `context_stack` compaction/type simplification, but that is not an active duplicate LLM context assembly path.

## Artifacts

- P133 result R123 and check C137.
- P134 result R142 and check C156.
- P135 result R160 and check C174.
- P136 result R165 and check C179.
- P137 result R170 and check C184.
- Primary mapped implementation areas:
  - `novaic-cortex/novaic_cortex/context_event_store.py`
  - `novaic-cortex/novaic_cortex/context_event_projection.py`
  - `novaic-cortex/novaic_cortex/context_event_read_model.py`
  - `novaic-cortex/novaic_cortex/workspace.py`
  - `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py`
  - `novaic-agent-runtime/task_queue/contracts/llm_call.py`
  - `novaic-agent-runtime/task_queue/utils/step_result_client.py`
  - `novaic-common/common/contracts/llm_assembly.py`
