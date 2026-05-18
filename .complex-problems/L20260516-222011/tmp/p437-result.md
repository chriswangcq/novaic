# Runtime bridge endpoint inventory result

## Summary

Inventoried the runtime-to-Cortex bridge surface for context, payload, step-result formatting, and LLM prepare calls. The live LLM prepare handler calls `/v1/context/prepare_for_llm`, while `/v1/context/read|append|batch` remain live bridge helpers used by `context.read` / `context.append` task handlers for materialized context projection and notification hint append. Those context endpoint ownership questions are unresolved here and intentionally carried into P438/P439.

## Done

- Saved endpoint/helper inventories for context, payload, and step-result projection paths.
- Saved representative source slices for `CortexBridge`, runtime context handlers, prepare handler, step-result client, and Cortex ContextEvent read model.
- Classified the main bridge categories:
  - `prepare_for_llm`: live LLM prepare path; calls Cortex ContextEvent-backed `/v1/context/prepare_for_llm`.
  - `read_context` / `append_context` / `append_context_batch`: live materialized context helpers used by runtime context handlers; unresolved ownership for P439.
  - `/v1/payload/*`: bounded explicit payload inspection, used by shell CLI.
  - `/v1/steps/read_formatted`: current tool-result projection endpoint used for current-turn/historical tool result formatting.
  - `display_perception` projection: current-turn multimodal/tool-result handoff surface, not a context projection endpoint.
- Spawned and closed P441 for a stale focused test fixture missing explicit `session_generation`.

## Verification

- Runtime bridge focused suite after P441 fix:

```text
36 passed in 0.15s
```

- Evidence artifacts:
  - `.complex-problems/L20260516-222011/tmp/p437/context-endpoint-callers.txt`
  - `.complex-problems/L20260516-222011/tmp/p437/payload-tool-result-callers.txt`
  - `.complex-problems/L20260516-222011/tmp/p437/cortex-bridge-slice.txt`
  - `.complex-problems/L20260516-222011/tmp/p437/context-handlers-slice.txt`
  - `.complex-problems/L20260516-222011/tmp/p437/cortex-prepare-handler-slice.txt`
  - `.complex-problems/L20260516-222011/tmp/p437/bridge-prepare-slice.txt`
  - `.complex-problems/L20260516-222011/tmp/p437/context-event-read-model-slice.txt`
  - `.complex-problems/L20260516-222011/tmp/p437/tool-result-format-endpoint-slice.txt`
  - `.complex-problems/L20260516-222011/tmp/p437/runtime-bridge-focused-pytest.after-fix.with-status.txt`

## Known Gaps

- P438 must prove the live agent loop LLM prepare path does not use `/v1/context/read` as the authoritative history source.
- P439 must decide ownership/migration for `/v1/context/read|append|batch` and `CortexBridge.read_context/append_context/append_context_batch`.
- P440 must perform the final bridge guard after those decisions.

## Artifacts

- Child cleanup closed: P441 / R418 / C444.
- Test fixture changed: `novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py`.
