# Audit context.jsonl projection role and callers

## Problem Definition

Workspace `context.jsonl` helpers still exist as materialized message projections. They must be clearly classified so they are not mistaken for the authoritative LLM context source and do not become a payload/base64 leakage path.

## Proposed Solution

Map the helper implementations, classify every active caller, and verify the LLM prepare/read-model path uses ContextEvent projections rather than `context.jsonl`. Split the work if implementation mapping, caller classification, and active prepare-path proof need independent closure.

## Acceptance Criteria

- `read_context`, `append_context`, `append_context_projection`, `append_context_batch`, and `append_context_batch_projection` are mapped.
- Active consumers/callers are listed and classified.
- Any active LLM context authority path reading `context.jsonl` is fixed or explicitly ruled out.
- Context write projection tests are identified and run.

## Verification Plan

Use `rg`/`nl` for helper and caller maps, run context-event read/projection/API tests, and add a residue guard if a direct `read_context` prepare-path risk exists.

## Risks

- Some old tests may intentionally exercise compatibility helpers, which should not be confused with production authority.
- A caller may read `context.jsonl` for display/debug and look suspicious; classification must be exact.

## Assumptions

- The desired authority path is ContextEvent/read-model, not `context.jsonl`.
- Materialized projections may remain if read-only/debug scoped and tested.
