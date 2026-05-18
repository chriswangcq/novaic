# Map ReAct saga source ordering

## Problem Definition

We need a source-level map of the ReAct saga step order proving how `prepare_context` relates to `call_llm`, including the payload-builder handoff through `prev_result`.

## Proposed Solution

Read `novaic-agent-runtime/task_queue/sagas/react_think.py` and the minimal supporting contract source needed to explain the handoff. Record line pointers for the saga step declarations, payload builders, and any branch or hook that could alter the order.

## Acceptance Criteria

- `prepare_context` and `call_llm` step declarations are mapped with source pointers.
- `_build_prepare_context_payload` and `_build_llm_call_payload` are mapped with source pointers.
- The `prev_result` handoff assumption is documented.
- Any source-level bypass around `prepare_context` before `call_llm` is classified.

## Verification Plan

- Use `nl -ba`/`sed` and `rg` to inspect the exact source slices.
- Optionally inspect the generic saga step model if needed to prove what `prev_result` means.
- Record result with source evidence and no code changes unless a real defect is discovered.

## Risks

- The source map alone does not protect future regressions; that is owned by sibling `P165`.
- Avoid overclaiming handler response shape; that is owned by `P160/P161`.

## Assumptions

- The saga definitions in `react_think.py` are the active ReAct think path.
