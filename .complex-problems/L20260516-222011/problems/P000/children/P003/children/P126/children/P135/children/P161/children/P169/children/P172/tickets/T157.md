# Verify LLM handler transport delegation boundary

## Problem Definition

`llm_handlers.py` must be IO orchestration only: parse explicit payload through `LLMCallInput`, prepare provider request through `prepare_llm_call`, then send via the business transport. It must not read Cortex context or reconstruct provider messages directly.

## Proposed Solution

Inspect `handlers/llm_handlers.py`, map the path from payload parsing to transport call, run existing static/behavior guard tests, and add a focused guard if direct context reads or provider-message assembly are not already covered.

## Acceptance Criteria

- Handler line pointers identify `LLMCallInput.from_payload`, `prepare_llm_call`, and the business transport call.
- Tests or static guards prove the handler contains no `read_context`/`context.read` authority path.
- The handler's preprocessing dependencies are explicitly injected into `prepare_llm_call`.
- Focused runtime handler tests are run.

## Verification Plan

Run `test_runtime_explicit_contracts.py` and `test_pr85_llm_context_smoke_guardrails.py`. Use source inspection to map exact handler lines.

## Risks

- Static source checks can miss dynamically named context reads, so source mapping must verify actual imports and call sites too.

## Assumptions

- Business transport internals are outside this leaf except for confirming the handler passes an already prepared request into transport.
