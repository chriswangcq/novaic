# LLM prepare path context authority audit success check

## Summary

`P154` is solved by `R138`. The audit proves the active prepare path is ContextEvent/read-model backed at Cortex, uses that prepared snapshot in runtime, and has tests guarding against fallback to `context.read`/`context.jsonl` authority.

## Evidence

- Cortex endpoint evidence from child `P156`:
  - `/v1/context/prepare_for_llm` uses `ContextEventReadModel(...).prepare()`.
  - The endpoint source does not call `read_context`.
  - Focused Cortex tests passed.
- Runtime caller evidence from child `P157`:
  - `react_think` runs `prepare_context` before `call_llm`.
  - `build_llm_call_payload` copies messages/tools from `prepare_context_result`.
  - `handle_cortex_prepare_llm_context` calls `bridge.prepare_for_llm(agent_root_scope_id)`.
  - `llm_handlers` sends `prepared.messages` from `prepare_llm_call`.
- Guard evidence from child `P158`:
  - Conflicting-snapshot behavior test prevents `context.read` projection from entering final messages.
  - Static guard prevents `read_result.context` from becoming the assembly input.
  - Final handler guard prevents direct `read_context`/`context.read` calls in `llm_handlers`.

## Criteria Map

- Active prepare-context/read-model path is mapped with source pointers: satisfied by child `P156` and `P157` source maps.
- Evidence proves it does not call `read_context` or parse `context.jsonl` as authority: satisfied by Cortex endpoint scan, runtime caller guard, and conflicting-snapshot test.
- If any authority read exists, it is fixed or split into a blocking child problem: no authority read was found; the only remaining `context.read` path is notification-hint insertion and is isolated by guards.

## Execution Map

- `T140` was a split ticket and all plan-time children are closed:
  - `P156` success check `C149`.
  - `P157` success check `C150`.
  - `P158` success check `C151`.
- `R138` aggregates those child results and records residual non-blocking naming risk.

## Stress Test

- Endpoint stress: tests exercise ContextEvent read model behavior rather than materialized context file fallback.
- Runtime stress: conflicting snapshot test proves stale `context.read` projection loses to prepared read-model snapshot.
- Regression stress: static source guards catch both prepare-handler and final-handler authority regressions.

## Residual Risk

- `context.read` remains an overloaded topic name. This is a clarity/API cleanup risk, not a solved-path authority risk, because final provider messages are now guarded away from that path.
- If a new LLM assembly route is added outside `react_think` and `llm_handlers`, it must add equivalent tests. Current active topic set points to the audited route.

## Result IDs

- R138
