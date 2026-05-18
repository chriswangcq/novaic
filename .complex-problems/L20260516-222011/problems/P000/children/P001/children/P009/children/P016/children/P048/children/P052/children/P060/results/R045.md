# Cortex Shell Projection Audit Result

## Summary

Audited Cortex step result projection and confirmed shell durable raw payloads are not rehydrated into normal LLM history. Cortex parses `tool-step-payload.v1` by recursively projecting `llm_content`, not `raw`.

## Done

- Inspected `novaic-cortex/novaic_cortex/step_result_projection.py`.
- Confirmed `parse_tool_result()` handles `tool-step-payload.v1` by calling `parse_tool_result(raw.get("llm_content", ""))`.
- Confirmed `tool-output.v1` projection uses `text`, artifacts, events, and errors, not durable raw shell stdout.
- Confirmed explicit display/image projection remains gated by display-specific modes, while history/current tool result projections call `_format_mcp_content(..., include_display=False)`.
- Confirmed test coverage includes `test_tool_step_payload_v1_projects_llm_content_not_raw_shell_payload`.

## Verification

- `cd novaic-cortex && PYTHONPATH=.:../novaic-logicalfs:../novaic-sandbox-sdk pytest -q tests/test_tool_output_projection.py tests/test_step_result_projection.py`
  - Passed: `14 passed`.

## Known Gaps

- This slice verifies Cortex projection behavior. The explicit large media-like shell stdout regression remains in sibling child `P061`.

## Artifacts

- `novaic-cortex/novaic_cortex/step_result_projection.py`
- `novaic-cortex/tests/test_tool_output_projection.py`
- `novaic-cortex/tests/test_step_result_projection.py`
