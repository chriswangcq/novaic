# P038 Result

## What Changed

- Replaced a generic `im_read` raw tool schema fixture in `novaic-common/tests/test_llm_assembly_contract.py` with `shell`.
- Replaced a generic `im_reply` error-observation fixture in `novaic-common/tests/test_cortex_observation_contract.py` with `shell`.
- Left `audio_qa` only in the explicit negative guard test that proves it is not an active builtin/LLM tool.

## Verification

- `PYTHONPATH=novaic-common pytest -q novaic-common/tests/test_cortex_observation_contract.py novaic-common/tests/test_llm_assembly_contract.py novaic-common/tests/test_tool_definitions_contract.py`
  - 23 passed
- Focused scan over `novaic-common/tests` now only finds `audio_qa` in negative guard assertions.

## Note

The first pytest attempt from inside `novaic-common` failed because `common` was not on `PYTHONPATH`; rerunning from the repo root with `PYTHONPATH=novaic-common` passed.
