# Prove LLM prepare path uses ContextEvent read model authority

## Problem Definition

The active LLM prepare path must not assemble model context from `context.jsonl`. It should use the ContextEvent/read-model authority path so stale materialized projections cannot leak into prompts.

## Proposed Solution

Map the Cortex `/v1/context/prepare_for_llm` endpoint, runtime bridge/client call, and runtime LLM assembly path. Add or run guard tests that prove `read_context` is not used as authority during prepare.

## Acceptance Criteria

- Active prepare endpoint and runtime caller are mapped with source pointers.
- Source/tests prove prepare uses ContextEvent/read-model, not `context.jsonl`.
- Any residue path reading `context.jsonl` for LLM context is fixed or split.

## Verification Plan

Use `rg`/`nl` to map code paths; run context read-model/projection tests and runtime LLM context smoke guardrails. Add a static guard if there is no existing one.

## Risks

- Runtime task named `context.read` may be confused with LLM prepare; classification must follow actual LLM call chain.

## Assumptions

- Materialized `context.jsonl` can exist for debug/projection while not being authoritative for LLM prompts.
