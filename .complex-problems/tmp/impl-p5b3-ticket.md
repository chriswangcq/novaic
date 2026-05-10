# Phase 5B3 Compatibility Wrapper Review And Removal

## Problem Definition

Phase 5B1/5B2 removed major file-walk authority residue, but `P045` still found live compatibility/legacy surfaces. The highest-risk area is `novaic_cortex.step_result_projection`: it still exports `format_for_llm` as a compatibility wrapper, and tests still encode migration-era wording around legacy MCP image/display behavior. This can mislead future code back into broad implicit projection behavior instead of the explicit `history/current/display/monitor` projection contract.

## Proposed Solution

Audit all current Cortex source/test hits for `compat`, `compatibility`, `legacy`, and `fallback`, then make a minimal but strict cleanup pass:

1. Identify which hits are intentional current mechanisms:
   - schema migrations in `operational_store.py`
   - guard tests proving removed legacy behavior
   - current public adapter behavior, if still genuinely required
2. Remove or rename stale compatibility wrappers:
   - Prefer deleting `format_for_llm` from public exports if all call sites can use explicit projection functions.
   - If external/public tests still require a transitional adapter, rename it to a current-contract name and remove “compatibility wrapper” wording.
3. Update all live call sites and tests to use explicit projection APIs:
   - `format_for_history_llm`
   - `format_for_current_tool_result_llm`
   - `format_for_display_perception_llm`
   - `format_for_monitor`
4. Rename tests that use “legacy” only as migration wording when the behavior is now a current explicit contract.
5. Add/keep static guards that prevent reintroducing broad compatibility/fallback projection language in live source while allowing justified migration code.

## Acceptance Criteria

- A source/test audit for `compat`, `compatibility`, `legacy`, and `fallback` is recorded in the result.
- `step_result_projection.py` no longer contains a “Compatibility wrapper” function or misleading compatibility wording.
- `novaic_cortex.__init__` exports only current-contract projection APIs.
- Live call sites in `api.py` and tests use explicit projection functions rather than a broad implicit wrapper.
- Remaining compatibility/legacy/fallback hits are either guard tests, schema migration internals, or explicitly justified current behavior.
- Targeted tests for step result projection, tool output projection, and context event no-compat behavior pass.

## Verification Plan

Run static searches and targeted tests:

```bash
rg -n "compat|compatibility|legacy|fallback|format_for_llm" novaic-cortex/novaic_cortex novaic-cortex/tests -S
PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q \
  novaic-cortex/tests/test_step_result_projection.py \
  novaic-cortex/tests/test_tool_output_projection.py \
  novaic-cortex/tests/test_resolve_for_llm.py \
  novaic-cortex/tests/test_context_event_no_compat.py
python3 -m py_compile novaic-cortex/novaic_cortex/step_result_projection.py novaic-cortex/novaic_cortex/api.py novaic-cortex/novaic_cortex/__init__.py
```

## Risks

- `format_for_llm` may be imported by code outside the Cortex package; if so, the execution result must either update that code or record a follow-up for external contract cleanup.
- Some “legacy” test names are guard tests and should not be blindly deleted.
- Migration code in `operational_store.py` is legitimate compatibility with persisted SQLite schema and should remain unless a full state reset is explicitly in scope.

## Assumptions

- The current desired contract is explicit projection mode selection, not a broad `include_display` boolean wrapper.
- Cortex source/test changes are in scope; external package updates are only in scope if static search finds direct imports in this workspace.
- Historical documentation cleanup belongs to Phase 5C unless it blocks source/test clarity.
