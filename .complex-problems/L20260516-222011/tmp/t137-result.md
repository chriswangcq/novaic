# Workspace context.jsonl projection map aggregate result

## Summary

Closed the split audit for `P143`. The `context.jsonl` helpers are mapped, active callers are classified, LLM prepare authority is proven to use ContextEvent/read-model snapshots, and focused projection/leakage regression tests pass.

## Done

- Incorporated `P152` / `R133` / `C147`:
  - Mapped `read_context`, `append_context`, `append_context_projection`, `append_context_batch`, and `append_context_batch_projection`.
  - Fixed corrupt materialized context projections so they fail visibly instead of silently skipping corrupt lines.
  - Added `test_read_context_rejects_corrupt_jsonl_projection`.
- Incorporated `P153` / `R134` / `C148`:
  - Classified all active non-test caller sites.
  - Fixed runtime `CortexBridge.read_context` fail-open behavior; it now fails closed instead of returning `[]` on corruption/error.
- Incorporated `P154` / `R138` / `C152`:
  - Proved Cortex `/v1/context/prepare_for_llm` uses ContextEvent/read-model authority.
  - Proved runtime LLM caller chain consumes the prepared snapshot, not `context.read` as provider-message authority.
  - Added behavior/static guards against `read_context`/`context.read` authority regression.
- Incorporated `P155` / `R139` / `C153`:
  - Identified and ran focused projection/read-model/leakage tests.
  - Cortex focused suite passed (`49 passed`).
  - Runtime focused suite passed (`35 passed`).

## Verification

- Child success checks:
  - `C147`, `C148`, `C152`, `C153`.
- Focused tests run across child tickets:
  - Cortex context projection/read-model suites: `38 passed`, `33 passed`, `49 passed` across focused combinations.
  - Runtime context/LLM authority suites: `31 passed`, `20 passed`, `10 passed`, `29 passed`, `35 passed` across focused combinations.
- Source classification:
  - Helpers are materialized projection/debug helpers.
  - Runtime `context.read` is notification-hint/idempotency support.
  - LLM prepare authority is ContextEvent/read-model, not `context.jsonl`.

## Known Gaps

- `context.read` is still a confusing topic name because it no longer means LLM context authority. This is a clarity/API cleanup risk, not a correctness blocker for the mapped boundary.
- Some docs/comments may still mention `context.jsonl` for persistence/projection behavior. They should be treated as projection/debug terminology unless tied to provider-message assembly.

## Artifacts

- Child packages under `P143`: `P152`, `P153`, `P154`, `P155`.
- Code changes from this branch include Cortex projection fail-closed behavior, runtime bridge fail-closed behavior, and runtime LLM authority guards.
