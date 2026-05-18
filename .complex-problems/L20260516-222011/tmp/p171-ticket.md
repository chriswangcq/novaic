# Verify LLMCall contract explicit provider payload source

## Problem Definition

The `LLMCallInput` and `prepare_llm_call` contract layer must assemble provider-bound messages/tools only from explicit payload fields plus injected preprocessing functions. Hidden context reads or global preprocessing would violate the new boundary.

## Proposed Solution

Inspect `contracts/llm_call.py`, map source fields and injected dependencies, tighten tests if needed, and run explicit-contract tests.

## Acceptance Criteria

- `LLMCallInput.from_payload` and `prepare_llm_call` are mapped with line pointers.
- Provider-bound `messages`, `tools`, `model`, and metadata sources are documented.
- Tests prove preprocessing functions are injected and ordered.
- No hidden context read or global sanitizer/multimodal path remains in the contract.

## Verification Plan

Run `test_runtime_explicit_contracts.py`; add direct assertions if message/tool source or preprocessing injection is weak.

## Risks

- Existing tests may focus on messages but not tools.

## Assumptions

- Handler-specific delegation belongs to sibling `P172`; this leaf focuses on the pure contract layer.
