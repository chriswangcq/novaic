# Runtime prepare-context handler chain mapped

## Summary

Consolidated the closed split audit for the runtime prepare-context handler chain. The live provider path is now mapped from ReAct saga ordering through Cortex `prepare_for_llm`, prepared snapshot handoff, final LLM payload assembly, and side-path classification. No active stale local continuity or `context.read` projection path remains in the audited provider-message authority chain.

## Handoff Map

1. Saga ordering:
   - `react_think` declares `prepare_context -> call_llm -> save_response`.
   - `call_llm` depends on `prepare_context`, so it receives the prepared result as an explicit dependency result.
2. Cortex prepare handler:
   - Runtime prepare handler calls `CortexBridge.prepare_for_llm(agent_root_scope_id)`.
   - Bridge target is `/v1/context/prepare_for_llm` with explicit tenant/scope payload.
   - The prepared response provides `messages`, `tools`, active stack metadata, and compatibility/provider fields.
3. LLM payload handoff:
   - `build_llm_call_payload` copies `messages` and `tools` from `prepare_context_result`.
   - `prepare_llm_call` receives explicit messages/tools and injected preprocessing dependencies.
   - Handler code delegates to the pure contract and has static guards against `context.read` as provider-message authority.
4. Continuity and `context.read` side paths:
   - `context.read` remains active-safe for explicit inspection and notification hints.
   - Wake/session continuity is active-safe current-input registration plus generation-checked attach.
   - Runtime production `read_context` callers were inventoried; no stale provider-input fallback was found.
5. Regression coverage:
   - Focused runtime coverage proves stale local messages/tools, `context.read` projections, no-wake replay, context-read ordering/by-id behavior, and historical/generic tool images cannot re-enter final LLM context incorrectly.

## Child Results

- `P159/R145`: saga ordering and DAG dependency handoff mapped; `call_llm.depends_on == ["prepare_context"]` guard added.
- `P160/R148`: Cortex prepare handler response and bridge endpoint contract mapped; bridge endpoint guard added.
- `P161/R154`: LLM payload handoff mapped through builder, contract, handler, and tests.
- `P162/R158`: local continuity and `context.read` residue classified as active-safe or non-provider-authority.
- `P163/R159`: focused regression coverage audit completed with `47 passed`.

## Verification

Focused tests run across the child audits:

- Saga/contract slice: `17 passed`.
- Prepare handler/bridge slices: `31 passed` and `26 passed`.
- LLM handoff slices: `13 passed`, `22 passed`, `31 passed`.
- Continuity/context-read slices: `31 passed`, `35 passed`, `41 passed`.
- Final P163 regression slice: `47 passed`.

## Known Gaps

No P135-specific gap remains. Live deployed service E2E, real provider transport, and real blob/display availability are intentionally broader product/runtime checks outside this handler-chain map.

## Artifacts

- `novaic-agent-runtime/task_queue/sagas/react_think.py`
- `novaic-agent-runtime/task_queue/contracts/react_think.py`
- `novaic-agent-runtime/task_queue/contracts/llm_call.py`
- `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py`
- `novaic-agent-runtime/task_queue/handlers/context_handlers.py`
- `novaic-agent-runtime/task_queue/handlers/llm_handlers.py`
- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
- `novaic-agent-runtime/tests/integration/test_saga_dag_refactor.py`
- `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`
- `novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py`
- `novaic-agent-runtime/tests/test_context_read_by_ids.py`
- `novaic-agent-runtime/tests/test_context_read_ordering.py`
- `novaic-agent-runtime/tests/test_pr113_no_wake_im_replay.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
- `novaic-agent-runtime/tests/test_pr67_wake_child_scope.py`
- `novaic-agent-runtime/tests/test_pr266_session_recovery_boundary.py`
