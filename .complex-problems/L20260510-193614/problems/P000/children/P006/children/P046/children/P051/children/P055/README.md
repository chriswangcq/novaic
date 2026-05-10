# Phase 5B3.4 Compatibility Residue Verification Gate

## Problem

After the wrapper/API cleanup and wording cleanup, we need a final gate proving remaining compatibility/legacy/fallback hits are intentional and that projection behavior still passes targeted tests.

## Success Criteria

- Static search for `compat`, `compatibility`, `legacy`, `fallback`, and broad projection helpers is reviewed and recorded.
- Any remaining hit has a current justification: schema migration, guard test, or public current adapter behavior.
- No broad `format_for_llm` compatibility wrapper remains unless explicitly justified by the earlier audit and renamed/documented as current contract.
- Targeted tests pass for `test_step_result_projection.py`, `test_tool_output_projection.py`, `test_resolve_for_llm.py`, and `test_context_event_no_compat.py`.
- Py compile passes for changed Cortex modules.
