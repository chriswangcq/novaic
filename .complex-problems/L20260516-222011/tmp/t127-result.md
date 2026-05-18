# Workspace materialized projections and payload reference map result

## Summary

Aggregated the closed split children for `P134`. The workspace materialized surfaces are now mapped as projections/retrieval aids rather than LLM context authority: payload storage/externalization, tool step normalization/indexing, `context.jsonl` projection behavior, and Cortex API materialization call sites all have evidence, focused tests, and non-blocking residual risks recorded.

## Done

- `P141/R124/C138` mapped payload write/read and blob externalization in `workspace.py`, including local JSON records, external blob records, manifest metadata, and read failure behavior.
- `P142/R132/C146` mapped tool step normalization, payload mirroring, compact step index metadata, corrupt index behavior, and active step-write call-site wiring.
- `P143/R140/C154` mapped `context.jsonl` helper functions, caller classification, runtime LLM prepare authority, and regression tests proving `ContextEventReadModel` is authoritative for LLM context.
- `P144/R141/C155` mapped Cortex API materialization call sites for context append/batch, step write, projection reads, formatted/preview reads, and payload APIs.
- Real fixes made by children include fail-loud corrupt JSONL handling, zero-duration/artifact index preservation, stricter tool-step shape validation, runtime `context.read` fail-closed behavior, and guard tests against `context.jsonl`/raw payload authority leaks.

## Verification

- Child success checks cited focused Cortex and Runtime pytest runs covering payload externalization, step indexes, context projection writes, ContextEvent read model, runtime LLM prepare guards, payload inspection APIs, and API step/context write contracts.
- Additional parent-level evidence comes from child checks:
  - `C138`: payload suites passed with `25 passed`.
  - `C146`: step normalization/index/call-site children closed with behavioral and static residue guards.
  - `C154`: context projection/read-model/runtime suites closed with focused Cortex and Runtime tests.
  - `C155`: API materialization map closed with `20 passed` and a duplicate-write-path stress search.

## Known Gaps

- `/v1/context/read` remains a confusing name for a materialized projection read surface. Current guards prove it is not provider-message authority, so this is API clarity debt rather than a blocking correctness issue.
- This parent result does not claim all backend cleanup is complete; it closes the workspace projection/payload map slice under `P134`.

## Artifacts

- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-cortex/novaic_cortex/api.py`
- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
- `novaic-agent-runtime/task_queue/sagas/react_think.py`
- `novaic-cortex/tests/test_step_index_outcome.py`
- `novaic-cortex/tests/test_context_event_api_steps_write.py`
- `novaic-cortex/tests/test_context_event_api_context_writes.py`
- `novaic-cortex/tests/test_payload_inspection_api.py`
- `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`
- `novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py`
