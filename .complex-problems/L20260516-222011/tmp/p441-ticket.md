# Ticket: Fix runtime bridge focused test fixture session_generation

## Problem Definition

The focused runtime bridge verification suite fails because one `test_pr85_llm_context_smoke_guardrails.py` fixture builds a React actions context without the now-required explicit positive `session_generation`.

## Proposed Solution

- Patch only the stale test fixture to include `session_generation`.
- Do not loosen production validation.
- Rerun the focused runtime bridge tests.

## Acceptance Criteria

- The failing test passes.
- The full focused runtime bridge suite from P437 passes.
- No production code changes are needed.

## Verification Plan

- Run the focused pytest command captured under P437.
- Optionally run a narrow grep/slice to show the patched fixture carries `session_generation`.

## Risks

- Accidentally masking a production boundary failure. Avoid this by changing only the fixture input.

## Assumptions

- Existing production validators are correct and should remain strict.
