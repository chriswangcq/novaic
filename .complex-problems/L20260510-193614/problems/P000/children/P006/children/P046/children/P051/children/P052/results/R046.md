# Phase 5B3.1 Compatibility Residue Audit Result

## Summary

Completed a read-only compatibility residue audit for Cortex source/tests. The main stale runtime surface is `step_result_projection.format_for_llm` plus its package export and tests. Most other hits are either intentional guard tests, schema migration internals, or explicit no-fallback boundary checks.

## Done

- Ran the source/test residue search for `compat`, `compatibility`, `legacy`, `fallback`, and `format_for_llm`.
- Ran a workspace-wide projection API import search across Cortex, runtime, business, common, logicalfs, sandbox-service, and sandbox-sdk.
- Inspected the highest-risk files:
  - `novaic-cortex/novaic_cortex/step_result_projection.py`
  - `novaic-cortex/novaic_cortex/__init__.py`
  - `novaic-cortex/novaic_cortex/api.py`
  - `novaic-cortex/tests/test_step_result_projection.py`
  - `novaic-cortex/tests/test_tool_output_projection.py`
  - selected guard/migration test files.

## Verification

- `rg -n "compat|compatibility|legacy|fallback|format_for_llm" novaic-cortex/novaic_cortex novaic-cortex/tests -S`
  - Result: found expected categories listed below.
- `rg -n "format_for_llm|format_for_history_llm|format_for_current_tool_result_llm|format_for_display_perception_llm" novaic-cortex novaic-agent-runtime novaic-business novaic-common novaic-logicalfs novaic-sandbox-service novaic-sandbox-sdk -S`
  - Result: direct `format_for_llm` use is limited to Cortex module export and Cortex tests; API live path already imports explicit projection functions.

## Audit Map

- Delete/rename in P053:
  - `novaic-cortex/novaic_cortex/step_result_projection.py`: `format_for_llm` is explicitly documented as a compatibility wrapper and should be removed.
  - `novaic-cortex/novaic_cortex/__init__.py`: package-level import/export of `format_for_llm` should be removed.
  - `novaic-cortex/tests/test_step_result_projection.py`: imports/tests `format_for_llm`; should switch to explicit projection functions.
  - `novaic-cortex/tests/test_tool_output_projection.py`: imports/tests `format_for_llm`; should switch to explicit projection functions.
  - `novaic-cortex/novaic_cortex/api.py`: live path already uses explicit functions, but the empty/unknown projection branch still honors `include_display`; P053 should decide whether to make projection explicit-only or keep this as a named current API adapter.
- Rename wording in P054:
  - `test_tool_output_projection.py`: migration-era names such as `test_legacy_mcp_image_still_uses_display_files_during_migration` and `test_explicit_projection_modes_control_legacy_display_files` describe current parsing/projection behavior and should be renamed.
  - `test_context_event_api_context_writes.py`: `preserves_legacy_behavior` appears to mean keyed retry compatibility; rename to idempotent retry/current behavior wording.
  - `context_stack/budget.py`: docstring still says "event-backed and legacy context preparation"; should be current-contract wording.
- Keep as current guard/no-fallback behavior:
  - `test_context_event_no_compat.py`: intentionally proves no DFS fallback when event stream is missing.
  - `test_context_event_read_source_guards.py`: intentionally proves no DFS/file-walk fallback.
  - `test_pr57_list_archived_summaries.py`, `test_legacy_skill_lifecycle_removed.py`, root-summary tests: guard deleted legacy APIs or stale meta precedence.
  - `sandbox.py` and sandbox tests: "no local fallback" is a desired explicit boundary, not residue.
  - `context_event_read_model.py`: reset-required error documents that legacy fallback is forbidden; current guard language is acceptable.
- Keep as current migration/schema code:
  - `operational_store.py`: `payload_manifest_legacy` migration is legitimate persisted SQLite schema migration code.
  - `test_context_event_store.py`: "initializes fresh root without legacy migration" is a current no-migration guard.
  - `test_operational_store.py`: "rejects memory fallback" is desired state authority behavior.
- Likely Phase 5C docs/comment cleanup, not P053 source API cleanup:
  - `main_cortex.py` comment about replacing deprecated FastAPI `on_event`; current explanatory comment.
  - Broader stale documentation mentions found outside this targeted source/test audit.

## Known Gaps

- No source code was changed in this audit ticket by design.
- P053 must remove/cut over the `format_for_llm` compatibility wrapper and package export.
- P054 must clean misleading source/test wording that is not a current guard.
- P055 must run the final static/targeted verification gate.

## Artifacts

- `.complex-problems/tmp/impl-p5b3-p1-result.md`
