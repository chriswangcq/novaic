# LLM prepare path context authority audit aggregate result

## Summary

Closed the split audit for `P154`. The Cortex endpoint, runtime caller chain, and regression guard layer all now prove the active LLM prepare path uses the ContextEvent/read-model authority rather than `context.jsonl`/`context.read` projection messages.

## Done

- Incorporated child `P156` / `R135` / `C149`:
  - Cortex `/v1/context/prepare_for_llm` is backed by `ContextEventReadModel.prepare()`.
  - Source scan proves the endpoint does not call `read_context`.
  - Focused Cortex tests passed (`33 passed`).
- Incorporated child `P157` / `R136` / `C150`:
  - Runtime chain mapped from `react_think.prepare_context` through `cortex.prepare_llm_context` into `llm.call`.
  - Final provider messages come from `prepare_context_result`, not `context.read`.
  - Added guard proving conflicting `context.read` projection is excluded from final messages.
  - Focused runtime tests passed (`20 passed` and `10 passed`).
- Incorporated child `P158` / `R137` / `C151`:
  - Added durable static and behavior guards against `read_context`/`context.read` authority regressions.
  - Cleaned stale `react_think` wording from `read context.jsonl` to `ContextEvent read model`.
  - Focused runtime guard tests passed (`29 passed`).

## Verification

- Child checks `C149`, `C150`, and `C151` are all success.
- Aggregate source map:
  - Cortex endpoint authority: `novaic-cortex/novaic_cortex/api.py:925`, `novaic-cortex/novaic_cortex/context_event_read_model.py`.
  - Runtime prepare caller: `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py:325`.
  - Runtime LLM payload construction: `novaic-agent-runtime/task_queue/contracts/react_think.py:98`.
  - Final LLM call: `novaic-agent-runtime/task_queue/handlers/llm_handlers.py:120`.
- Aggregate tests:
  - Cortex read-model/projection tests: `33 passed`.
  - Runtime prepare/caller tests: `20 passed` + `10 passed`.
  - Runtime guard/tool-path tests: `29 passed`.

## Known Gaps

- `context.read` remains an active runtime topic for environment notification hint insertion and idempotency scanning. It is no longer LLM prepare authority, but the topic name is confusing and could be renamed in a separate API cleanup.
- Some persistence comments still mention `context.jsonl` for non-authority projection/debug behavior. They are outside this prepare-authority audit unless they feed provider messages.

## Artifacts

- Child results/checks:
  - `P156`: `R135`, `C149`
  - `P157`: `R136`, `C150`
  - `P158`: `R137`, `C151`
- Code/test files touched in this audit:
  - `novaic-cortex/novaic_cortex/workspace.py`
  - `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
  - `novaic-agent-runtime/task_queue/sagas/react_think.py`
  - `novaic-cortex/tests/test_context_event_api_context_writes.py`
  - `novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py`
  - `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`
