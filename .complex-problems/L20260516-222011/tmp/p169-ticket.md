# Verify LLM handler provider request assembly

## Problem Definition

After `react_think` builds the `llm.call` payload, `llm_handlers` and `contracts/llm_call.py` prepare the final provider request. This layer must treat the payload as the only message/tool authority and avoid hidden reads from Cortex, continuity state, or global preprocessing hooks.

## Proposed Solution

Inspect `handlers/llm_handlers.py` and `contracts/llm_call.py`, map the handoff from `LLMCallInput.from_payload` through `prepare_llm_call`, and add or tighten tests that prove final provider messages/tools are derived from explicit payload fields.

## Acceptance Criteria

- Handler and contract files have line pointers for payload parsing and provider request assembly.
- The final `messages` and `tools` source is documented.
- Tests or static guards fail if handler code reads Cortex context or bypasses the explicit contract module.
- Focused runtime tests are run.

## Verification Plan

Run explicit contract tests and LLM context smoke guardrail tests. Add a minimal test if provider `tools` or `messages` source authority is not directly guarded.

## Risks

- The handler may delegate correctly while preprocessing functions mutate messages; this ticket must distinguish explicit injected preprocessing from hidden context reads.
- Static source guards can be brittle; behavioral assertions should be preferred when practical.

## Assumptions

- This leaf remains bounded to runtime handler/provider request assembly; UI/log visibility and multimodal display handling are outside scope.
