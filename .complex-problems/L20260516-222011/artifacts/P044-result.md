# P044 Result

## What Changed

- Changed `test_pr70_explicit_skill_summary_only.py` wording from memory inference from `im_reply` to memory inference from reply actions.
- Kept `test_pr85_llm_context_smoke_guardrails.py` negative assertion that `im_reply` is absent from LLM tool schema.

## Verification

- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr70_explicit_skill_summary_only.py tests/test_pr85_llm_context_smoke_guardrails.py`
  - 10 passed
- Runtime test scan now leaves:
  - `LEGACY_DIRECT_REPLY_TOOL = "im_reply"` in finalizer legacy-negative fixture.
  - `assert "im_reply" not in tool_names` as an explicit schema denylist guard.

## Remaining Gap

Parent runtime fixture problem still needs aggregate closure after its children close.
