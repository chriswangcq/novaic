# Phase 5B3.4 Compatibility Residue Verification Gate

## Problem Definition

After audit, wrapper removal, and wording cleanup, we need a final gate proving there is no misleading compatibility residue left in current Cortex source/tests. Remaining hits must be intentional and documented, not accidental leftovers.

## Proposed Solution

Perform a strict verification pass:

1. Re-run static searches for `compat`, `compatibility`, `legacy`, `fallback`, and `format_for_llm`.
2. Confirm no broad projection wrapper remains.
3. Categorize every remaining hit as one of:
   - persisted schema migration
   - negative guard test
   - explicit no-fallback boundary
   - current adapter behavior
4. Inspect `/v1/steps/read_formatted` `include_display` branch and decide whether it is a justified current adapter or a follow-up problem.
5. Run targeted tests and py-compile checks.

## Acceptance Criteria

- `format_for_llm` has no matches in Cortex or sibling packages.
- Remaining `legacy`/`fallback`/`compat` hits are documented with current justification.
- If `include_display` is judged stale compatibility residue, create a follow-up via check-success; otherwise record why it is current adapter behavior.
- Targeted projection/no-compat tests pass.
- Py compile passes for changed Cortex modules.

## Verification Plan

```bash
rg -n "format_for_llm" novaic-cortex novaic-agent-runtime novaic-business novaic-common novaic-logicalfs novaic-sandbox-service novaic-sandbox-sdk -S
rg -n "compat|compatibility|legacy|fallback" novaic-cortex/novaic_cortex novaic-cortex/tests -S
PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q \
  novaic-cortex/tests/test_step_result_projection.py \
  novaic-cortex/tests/test_tool_output_projection.py \
  novaic-cortex/tests/test_resolve_for_llm.py \
  novaic-cortex/tests/test_context_event_no_compat.py \
  novaic-cortex/tests/test_context_event_read_source_guards.py \
  novaic-cortex/tests/test_context_event_api_context_writes.py
python3 -m py_compile novaic-cortex/novaic_cortex/step_result_projection.py novaic-cortex/novaic_cortex/__init__.py novaic-cortex/novaic_cortex/api.py novaic-cortex/novaic_cortex/context_stack/budget.py
```

## Risks

- The verification may find that `include_display` is still compatibility residue. If so, do not bury it; record a follow-up from the check.
- Static hit counts alone are insufficient; every remaining hit needs semantic classification.

## Assumptions

- This is a verification gate, not broad implementation. It may perform only small fixes if the issue is obvious and directly within the gate; larger work must become follow-up.
