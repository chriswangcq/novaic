# Cortex explicit projection modes result

## Summary

Implemented explicit projection modes across Cortex and Runtime step-ref expansion. Runtime now sends a semantic `projection` value instead of using current-round `include_display` as the business decision.

## Done

- Updated `novaic-cortex/novaic_cortex/step_result_projection.py`:
  - added `format_for_history_llm()`;
  - added `format_for_current_tool_result_llm()`;
  - added `format_for_display_perception_llm()`;
  - added `format_for_monitor()`;
  - kept `format_for_llm()` as a compatibility wrapper only.
- Updated `novaic-cortex/novaic_cortex/api.py` to accept `projection` and dispatch to the explicit projection function.
- Updated `novaic-agent-runtime/task_queue/utils/cortex_bridge.py` to pass `projection`.
- Updated `novaic-agent-runtime/task_queue/utils/step_result_client.py`:
  - `history` for old-round tool messages;
  - `current_tool_result` for current non-display tools;
  - `display_perception` only for current explicit `display`.
- Added/updated tests for Cortex projection modes and Runtime projection selection.

## Verification

- `cd novaic-cortex && python -m pytest tests/test_tool_output_projection.py tests/test_step_result_projection.py -q`
  - Result: `11 passed in 0.04s`.
- `cd novaic-agent-runtime && python -m pytest tests/test_pr71_no_tool_retry_context_cleanup.py tests/test_runtime_explicit_contracts.py tests/test_pr85_llm_context_smoke_guardrails.py -q`
  - Result: `26 passed in 0.12s`.
- Residue search:
  - `rg "include_display = \\(current_round_id"` found no matches.
  - Explicit projection names are present in Cortex API/projection and Runtime client tests.

## Residual Risk

- The compatibility wrapper `format_for_llm(include_display=...)` remains for older direct callers/tests. A later deletion ticket should remove or quarantine it once all callers use explicit projection functions.
