# Ticket: clean common contract test fixtures

## Problem Definition

Common tests have a few direct-tool names in generic fixtures and negative guard assertions. Generic fixtures should move to final harness/shell-first names; negative guard assertions can keep migrated names if the intent is explicit.

## Proposed Solution

- Replace generic `im_read` schema fixture in LLM assembly test with `shell`.
- Replace generic error-observation fixture from `im_reply` to an active/final tool.
- Keep `audio_qa` negative assertions as migrated-shell-capability guard coverage.

## Acceptance Criteria

- `novaic-common/tests/test_llm_assembly_contract.py` no longer uses direct IM tools as a normal schema example.
- `novaic-common/tests/test_cortex_observation_contract.py` no longer uses direct IM tools as a generic error-observation example.
- `audio_qa` appears only in explicit negative guard naming in common tests.
- Focused common tests pass.

## Verification Plan

- Focused `rg` over `novaic-common/tests`.
- Run touched common tests.

## Risk

Do not remove negative guard coverage proving `audio_qa` is not an active builtin tool.
