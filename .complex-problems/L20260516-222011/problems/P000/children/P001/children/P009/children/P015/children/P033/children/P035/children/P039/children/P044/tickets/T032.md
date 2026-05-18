# Ticket: clean runtime guard and smoke assertion wording

## Problem Definition

Runtime guard tests still mention `im_reply`. One hit is an explicit negative assertion that should remain; another is a comment that should describe the modern reply action concept rather than the old direct tool.

## Proposed Solution

- Change PR-70 comment wording from `im_reply` to reply action.
- Keep PR-85 negative assertion that `im_reply` is absent from the LLM tool schema.
- Verify runtime test scan and focused tests.

## Acceptance Criteria

- Runtime guard comments do not describe old direct tools as active paths.
- Negative assertions keep old names only as denylist checks.
- Focused guard tests pass.

## Verification Plan

- Focused `rg` over runtime tests.
- Run `test_pr70_explicit_skill_summary_only.py` and `test_pr85_llm_context_smoke_guardrails.py`.

## Risk

Do not remove the negative schema assertion for the removed direct tool.
