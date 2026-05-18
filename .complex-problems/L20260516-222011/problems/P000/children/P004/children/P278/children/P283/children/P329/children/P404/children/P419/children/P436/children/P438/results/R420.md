# Agent loop prepare-path proof result

## Summary

Proved the live agent loop LLM prepare path uses the Cortex ContextEvent-backed `/v1/context/prepare_for_llm` snapshot, not the materialized `/v1/context/read` projection as authoritative history. No source change was needed for P438.

## Done

- Traced `react_think` saga to `TaskTopics.CORTEX_PREPARE_LLM_CONTEXT`, then to `handle_cortex_prepare_llm_context`, `CortexBridge.prepare_for_llm`, and `LLM_CALL`.
- Saved source slices for the saga, runtime prepare handler, bridge prepare method, Cortex ContextEvent read model, and guard tests.
- Verified runtime guard test that poisons `bridge.read_context` with `"legacy context.read projection"` while `bridge.prepare_for_llm` returns `"prepared read-model snapshot"`; final messages include only the prepared snapshot.
- Verified Cortex guard tests that ensure `/v1/context/prepare_for_llm` has `ContextEventReadModel` and no `read_context`/DFS fallback.

## Verification

Runtime focused tests:

```text
29 passed in 0.16s
```

Cortex focused tests:

```text
15 passed in 0.41s
```

## Known Gaps

- P439 still needs to decide ownership/migration for materialized context endpoints and `CortexBridge.read_context/append_context/append_context_batch`.
- P440 still needs final bridge guard verification after P439.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p438/react-think-saga-slice.txt`
- `.complex-problems/L20260516-222011/tmp/p438/prepare-handler-slice.txt`
- `.complex-problems/L20260516-222011/tmp/p438/bridge-prepare-slice.txt`
- `.complex-problems/L20260516-222011/tmp/p438/context-event-read-model-prepare-slice.txt`
- `.complex-problems/L20260516-222011/tmp/p438/runtime-prepare-guard-test-slice.txt`
- `.complex-problems/L20260516-222011/tmp/p438/cortex-read-source-guard-test-slice.txt`
- `.complex-problems/L20260516-222011/tmp/p438/runtime-prepare-focused-pytest.with-status.txt`
- `.complex-problems/L20260516-222011/tmp/p438/cortex-prepare-focused-pytest.with-status.txt`
