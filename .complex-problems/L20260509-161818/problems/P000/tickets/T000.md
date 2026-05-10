# Pass current round ID into step-ref expansion

## Problem Definition

`expand_messages_for_llm()` already accepts `current_round_id`, but `prepare_llm_call()` does not pass it. That leaves the expansion dependency without the explicit round boundary needed to decide whether display content is current-turn or historical.

## Proposed Solution

Update `prepare_llm_call()` to pass `current_round_id=source.round_id` into `expand_messages_for_llm`. Extend the explicit contract test to assert this argument is supplied.

## Acceptance Criteria

- Current round ID is passed as an explicit input.
- Test covers the dependency call arguments.
- Existing Runtime LLM contract tests pass.

## Verification Plan

- Run `python -m pytest tests/test_runtime_explicit_contracts.py -q`.
- Run Runtime context smoke guard tests.

## Risks

- Some tests may assume the old missing kwarg; update them to the intended contract.

## Assumptions

- `source.round_id` is the canonical round ID for the LLM call being prepared.
