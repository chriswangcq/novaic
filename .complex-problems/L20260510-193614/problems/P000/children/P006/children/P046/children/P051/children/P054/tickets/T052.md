# Phase 5B3.3 Legacy Test And Comment Wording Cleanup

## Problem Definition

After the API cutover, several live tests/comments still use `legacy` wording for behavior that is now current-contract behavior. Some other `legacy` wording is intentionally a guard proving old behavior is removed. The misleading wording should be removed without weakening guard tests.

## Proposed Solution

Use the P052 audit map and static search to clean only misleading source/test wording:

1. Rename projection tests where `legacy` describes current explicit parsing/projection behavior.
2. Rename keyed-retry test wording from `preserves_legacy_behavior` to current idempotent retry behavior.
3. Update source comments/docstrings that refer to legacy context preparation when the current code is event-backed/budget behavior.
4. Keep guard tests that explicitly assert old legacy routes/fallbacks are removed.
5. Re-run residue search and targeted tests.

## Acceptance Criteria

- Live test names no longer use `legacy` for current behavior.
- `context_stack/budget.py` top-level docstring no longer advertises legacy context preparation.
- Guard tests that intentionally mention legacy removed/fallback behavior remain intact.
- Static search output has fewer misleading legacy hits and remaining hits are explainable.
- Targeted tests pass.

## Verification Plan

```bash
rg -n "legacy|fallback|compat|compatibility" novaic-cortex/novaic_cortex novaic-cortex/tests -S
PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q \
  novaic-cortex/tests/test_tool_output_projection.py \
  novaic-cortex/tests/test_context_event_api_context_writes.py \
  novaic-cortex/tests/test_context_event_no_compat.py \
  novaic-cortex/tests/test_context_budget.py \
  novaic-cortex/tests/test_pr56_root_scope_summary.py \
  novaic-cortex/tests/test_pr57_list_archived_summaries.py
python3 -m py_compile novaic-cortex/novaic_cortex/context_stack/budget.py
```

## Risks

- Blindly deleting `legacy` from guard tests would hide important “old path must stay removed” checks.
- Some string literals deliberately simulate stale legacy metadata and should remain if they make the guard clearer.

## Assumptions

- This ticket is limited to source/test wording and names, not historical docs.
- Actual compatibility code deletion was handled by P053.
