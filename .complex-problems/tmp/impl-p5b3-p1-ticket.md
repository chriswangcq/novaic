# Phase 5B3.1 Compatibility Residue Audit Map

## Problem Definition

The compatibility cleanup must start with evidence, not assumptions. Current search hits include migration internals, source comments, guard tests, and possible stale wrappers. We need a categorized map before deleting code.

## Proposed Solution

Run bounded static inspection over Cortex source/tests for the relevant residue terms, inspect the highest-risk files (`step_result_projection.py`, `__init__.py`, `api.py`, projection tests, no-compat tests), and record a categorized decision table:

- keep as current migration/schema code
- keep as guard test
- delete/rename in later child problem
- needs external import check

The result should explicitly name the work that P053/P054/P055 must perform.

## Acceptance Criteria

- All source/test hits for `compat`, `compatibility`, `legacy`, `fallback`, and `format_for_llm` are inspected or grouped with a justified pattern.
- `step_result_projection.format_for_llm` is classified with a specific next action.
- Projection tests and context-event no-compat tests are classified.
- Legitimate migration code is separated from stale compatibility residue.
- No code changes are made except the result/check artifacts.

## Verification Plan

Use:

```bash
rg -n "compat|compatibility|legacy|fallback|format_for_llm" novaic-cortex/novaic_cortex novaic-cortex/tests -S
rg -n "format_for_llm|format_for_history_llm|format_for_current_tool_result_llm|format_for_display_perception_llm" novaic-cortex novaic-agent-runtime novaic-business novaic-common novaic-logicalfs novaic-sandbox-service novaic-sandbox-sdk -S
```

Then inspect selected files with `nl -ba` slices and record the categorized audit in the result.

## Risks

- Broad static searches can include historical or intentional guard language; the audit must classify rather than blindly remove.
- External import checks may reveal cleanup outside `novaic-cortex`, which should be recorded for P053 if direct workspace imports exist.

## Assumptions

- This ticket is read-only audit work.
- Deletion/rename work is intentionally deferred to child implementation problems.
