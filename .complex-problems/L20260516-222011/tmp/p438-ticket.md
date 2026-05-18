# Ticket: Prove live agent loop LLM prepare path

## Problem Definition

The live agent loop must assemble LLM requests from the authoritative ContextEvent-backed prepare snapshot, not from stale materialized `context.jsonl` projection reads. P437 identified both `/v1/context/prepare_for_llm` and `/v1/context/read` as live bridge surfaces; this ticket proves which one feeds LLM calls.

## Proposed Solution

- Trace `react_think` saga tasks through `CORTEX_PREPARE_LLM_CONTEXT`, `handle_prepare_llm_context`, `CortexBridge.prepare_for_llm`, and `LLM_CALL`.
- Inspect the runtime assembler and Cortex read model source slices.
- Run existing prepare-path guard tests.
- Add a regression test if current tests do not directly assert that `handle_prepare_llm_context` uses `prepare_for_llm` and not `read_context`.

## Acceptance Criteria

- Source evidence shows live LLM request messages come from `bridge.prepare_for_llm(...)`.
- Source evidence shows Cortex `/v1/context/prepare_for_llm` prepares from `ContextEvent` stream/read model.
- Runtime tests/guards prove `read_context` is not used as the LLM prepare history source.
- Any discovered bypass is fixed or split.

## Verification Plan

- Run targeted `rg` and source slices for `react_think`, `handle_prepare_llm_context`, `assemble_llm_request_from_snapshot`, `prepare_for_llm`, and `read_context`.
- Run focused runtime and Cortex prepare-path tests.
- Add or adjust tests only if the current proof is incomplete.

## Risks

- `context.read` may still legitimately append notification hints. Do not conflate notification injection with LLM request assembly.

## Assumptions

- P439 will handle ownership/migration for materialized context endpoints that are not authoritative LLM prepare sources.
