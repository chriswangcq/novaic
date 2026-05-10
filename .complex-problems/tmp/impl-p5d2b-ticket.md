# Phase 5D.2b Step Formatting And Sandbox Contract Guard Coverage

## Problem Definition

Verify guard coverage for public step formatting and sandbox path contracts. Public step formatting must use explicit `projection`; `include_display` must stay an internal resolver detail only. Shell commands must reject ephemeral `novaic-cortex-sandbox-*` backing paths and guide users to stable `/cortex/ro` / `/cortex/rw` paths.

## Proposed Solution

- Search tests for public step projection API guards and sandbox path rejection.
- Run relevant tests.
- Add a minimal guard if unsupported public `include_display` or backing-path rejection is not covered.

## Acceptance Criteria

- Guard coverage map is recorded for step formatting public API and sandbox path rejection.
- Relevant tests pass.
- Low-level `include_display` internals are explicitly classified separately from public API.

## Verification Plan

```bash
rg -n "unsupported_step_projection|projection|include_display|novaic-cortex-sandbox-|Cortex shell paths under" novaic-cortex/tests novaic-cortex/novaic_cortex -S
pytest -q <relevant tests>
```

## Risks

- `include_display` appears in low-level `resolve_for_llm`; do not delete it unless it is public API residue.

## Assumptions

- This ticket does not change shell architecture; it only verifies/guards contracts.
