# Verify ReactThink prepared snapshot payload builder

## Problem Definition

`build_llm_call_payload` must copy `messages` and `tools` from `prepare_context_result` into the `llm.call` payload, while keeping saga-local fields limited to metadata such as ids, round, generation, and retry counters.

## Proposed Solution

Inspect `contracts/react_think.py`, map `ReactThinkInput` and `build_llm_call_payload`, and run or add focused explicit-contract tests proving prepared messages/tools are the source of truth.

## Acceptance Criteria

- Source line pointers identify `build_llm_call_payload` and its copied fields.
- The field map separates prepared snapshot fields from saga metadata fields.
- Tests prove `messages` and `tools` come from the prepare result.
- No local context fallback is found in the builder.

## Verification Plan

Run `test_runtime_explicit_contracts.py` after source inspection. Add a minimal assertion if the existing test does not directly distinguish prepare-result messages/tools from saga-local fields.

## Risks

- Existing tests may pass identical values and therefore fail to prove source authority.

## Assumptions

- This problem is narrow enough for one-go if the existing test already uses distinct prepared values or can be tightened with a small assertion.
