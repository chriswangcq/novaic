# Verify CortexBridge prepare_for_llm endpoint contract

## Problem Definition

`CortexBridge.prepare_for_llm` is the runtime-side client method that should call the ContextEvent-backed Cortex prepare endpoint. The audit must prove the endpoint path, tenant payload, and passthrough return shape, and must catch any active fallback from prepare into `read_context`.

## Proposed Solution

Inspect `novaic-agent-runtime/task_queue/utils/cortex_bridge.py` and the runtime LLM context handler tests. Add or tighten a focused unit contract test if the bridge endpoint path is not directly guarded. Run the bridge/handler-focused test slice and record exact evidence pointers.

## Acceptance Criteria

- The `prepare_for_llm` implementation has file/line evidence for endpoint path and payload fields.
- The result passthrough shape is covered by a focused test or equivalent direct evidence.
- Any active fallback to `read_context` from prepare is either absent by inspection or fixed before result recording.
- Focused runtime bridge/handler tests are run and reported.

## Verification Plan

Run targeted runtime tests covering `CortexBridge`, LLM context preparation, and wake child scope behavior with explicit `PYTHONPATH`. Use skeptical one-go checking: if endpoint path or passthrough behavior is not directly tested, add a minimal regression test before recording the result.

## Risks

- Existing handler tests may mock `prepare_for_llm` and miss the actual HTTP path.
- A text search may miss an indirect fallback unless `prepare_for_llm`, `read_context`, and handler call sites are checked together.

## Assumptions

- Runtime bridge endpoint contracts belong in `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py` unless a more specific bridge test file already exists.
- This ticket should remain narrow; broader runtime LLM payload handoff and continuity-read residue are separate sibling problems.
