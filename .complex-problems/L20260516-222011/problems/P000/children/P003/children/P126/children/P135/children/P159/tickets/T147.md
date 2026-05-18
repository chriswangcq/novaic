# Map ReAct saga prepare-context ordering

## Problem Definition

`react_think.py` wires the queue saga step graph. We need to prove `prepare_context` runs before `call_llm`, and that `call_llm` receives the previous prepare result rather than stale local context or an optional bypass path.

## Proposed Solution

Inspect `novaic-agent-runtime/task_queue/sagas/react_think.py` and the nearby `react_think` contract entrypoints that the saga calls. Map each relevant step, dependency, and payload builder. Verify whether any branch can call the LLM without a prepare-context result. Add a focused ordering/static guard if current tests do not pin this contract.

## Acceptance Criteria

- Source pointers identify the saga step list and ordering for `prepare_context` and `call_llm`.
- The `prev_result`/step-result dependency passed into `build_llm_call_payload` is documented.
- Any skip/bypass branch around `prepare_context` is classified as active-safe, dead, or stale.
- Focused tests or static guards covering prepare-before-LLM ordering are identified and run.

## Verification Plan

- Inspect `react_think.py` line-numbered slices around saga step definitions and payload builders.
- Inspect `contracts/react_think.py` for `build_llm_call_payload`.
- Run focused runtime tests that cover ReAct saga payload construction and LLM context smoke guardrails.
- Add a static guard if no existing test asserts ordering.

## Risks

- Existing tests may validate payload shape but not saga ordering. If so, add a small guard instead of assuming source shape is stable.
- Other sibling problems own handler response shape and continuity residue; do not overclaim those here.

## Assumptions

- `prepare_context` is the intended immediate predecessor for LLM message/tool input.
- The saga engine passes the previous step result into a step's `build_payload` callback.
