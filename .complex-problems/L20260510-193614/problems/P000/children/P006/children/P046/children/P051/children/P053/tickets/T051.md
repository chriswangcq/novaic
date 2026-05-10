# Phase 5B3.2 Step Projection Explicit API Cutover

## Problem Definition

`step_result_projection.format_for_llm` is still a compatibility wrapper with `include_display`; package exports and tests use it. This conflicts with the current explicit projection-mode contract and can reintroduce ambiguous display/history behavior.

## Proposed Solution

Remove the broad wrapper from the current public API and update all internal/tests to explicit projection functions:

1. Delete `format_for_llm` from `step_result_projection.py`.
2. Remove `format_for_llm` import/export from `novaic_cortex.__init__`.
3. Update `test_step_result_projection.py`:
   - truncation/history checks use `format_for_history_llm` or `format_for_current_tool_result_llm`.
   - data-url visual checks use `format_for_display_perception_llm`.
4. Update `test_tool_output_projection.py`:
   - artifact manifest checks use `format_for_display_perception_llm` when asserting even display perception does not inline artifact images.
   - remove broad wrapper import.
5. Verify API live path already uses explicit projection functions; if any fallback branch is still broad, either make it explicitly named current adapter behavior or remove it if tests prove it is unused.

## Acceptance Criteria

- `novaic_cortex.step_result_projection` has no `format_for_llm` function.
- `novaic_cortex.__init__` no longer imports/exports `format_for_llm`.
- No Cortex source/test imports `format_for_llm`.
- Projection behavior remains covered by explicit history/current/display tests.
- Targeted projection tests pass.

## Verification Plan

```bash
rg -n "format_for_llm" novaic-cortex/novaic_cortex novaic-cortex/tests -S
PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q \
  novaic-cortex/tests/test_step_result_projection.py \
  novaic-cortex/tests/test_tool_output_projection.py \
  novaic-cortex/tests/test_resolve_for_llm.py
python3 -m py_compile novaic-cortex/novaic_cortex/step_result_projection.py novaic-cortex/novaic_cortex/__init__.py novaic-cortex/novaic_cortex/api.py
```

## Risks

- If hidden external users import `format_for_llm`, removing the export is breaking. The audit found no workspace sibling imports; this ticket optimizes for no compatibility residue, matching the current cleanup principle.
- The `/v1/steps/read_formatted` API still has `include_display`; changing request schema may be broader than this ticket. If the branch remains, it must not depend on `format_for_llm`.

## Assumptions

- Internal workspace code is the authoritative compatibility boundary for this cleanup.
- Explicit projection functions are the desired current API.
