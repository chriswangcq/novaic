# Phase 5B3.4 Compatibility Residue Verification Gate Result

## Summary

The verification gate confirmed the `format_for_llm` compatibility wrapper is gone and targeted tests pass, but it found one real remaining compatibility-style API surface: `include_display` is still carried through runtime step-result formatting into Cortex as a boolean projection switch. This should not be accepted as final explicit-projection state.

## Done

- Re-ran workspace-wide static search for `format_for_llm`.
- Re-ran Cortex source/test static search for `compat`, `compatibility`, `legacy`, and `fallback`.
- Inspected `StepFormattedRequest` and `/v1/steps/read_formatted`.
- Inspected runtime callers in:
  - `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
  - `novaic-agent-runtime/task_queue/utils/step_result_client.py`
  - `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py`
- Ran targeted projection/no-compat tests and compile checks.

## Verification

- `rg -n "format_for_llm" novaic-cortex novaic-agent-runtime novaic-business novaic-common novaic-logicalfs novaic-sandbox-service novaic-sandbox-sdk -S`
  - Result: no matches.
- `rg -n "compat|compatibility|legacy|fallback" novaic-cortex/novaic_cortex novaic-cortex/tests -S`
  - Result: remaining hits are explainable except that they led to the `include_display` adapter inspection.
- Targeted tests:
  - `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_step_result_projection.py novaic-cortex/tests/test_tool_output_projection.py novaic-cortex/tests/test_resolve_for_llm.py novaic-cortex/tests/test_context_event_no_compat.py novaic-cortex/tests/test_context_event_read_source_guards.py novaic-cortex/tests/test_context_event_api_context_writes.py`
  - Result: `35 passed in 0.33s`.
- Compile check:
  - `python3 -m py_compile novaic-cortex/novaic_cortex/step_result_projection.py novaic-cortex/novaic_cortex/__init__.py novaic-cortex/novaic_cortex/api.py novaic-cortex/novaic_cortex/context_stack/budget.py`
  - Result: passed.

## Remaining Hit Classification

- Legitimate schema migration:
  - `operational_store.py` uses `payload_manifest_legacy` for SQLite schema migration.
- Negative guard tests:
  - no-compat/no-DFS-fallback tests
  - deleted legacy JWT/root-summary route tests
  - compact alias and tool schema fallback guard tests
- Explicit no-fallback boundary:
  - sandbox local fallback rejection
  - operational store memory fallback rejection
- Current reset-required wording:
  - `ContextEventReadModelResetRequired` says legacy fallback is forbidden, which describes the negative contract.
- Blocker:
  - `StepFormattedRequest.include_display`, `CortexBridge.read_step_formatted(include_display=...)`, and `step_result_client` still carry boolean projection selection. The current architecture should use explicit `projection` only.

## Known Gaps

- The gate is not successful until `include_display` is removed from the Cortex/runtime step-formatting path and tests assert explicit projection-only behavior.

## Artifacts

- `.complex-problems/tmp/impl-p5b3-p4-result.md`
