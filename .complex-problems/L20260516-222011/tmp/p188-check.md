# P188 Check: Cortex display projection contract

## Summary

Success. R173 satisfies P188's Cortex-local criteria: display parsing/formatting paths are mapped, explicit display perception can emit image `_mcp_content`, and history/current-tool formatting remains text-only. The remaining provider/runtime questions are separate sibling problems and are not hidden inside this check.

## Evidence

- `step_result_projection.py` maps the core boundary:
  - `parse_tool_result` parses `_mcp_content` image data into `display_files`.
  - `format_for_history_llm` and `format_for_current_tool_result_llm` call `_format_mcp_content` with `include_display=False`.
  - `format_for_display_perception_llm` calls `_format_mcp_content` with `include_display=True`.
- `/v1/steps/read_formatted` in `novaic-cortex/novaic_cortex/api.py` explicitly selects `history`, `current_tool_result`, or `display_perception`.
- Focused tests pass:
  - `15 passed` for Cortex projection tests.
  - `9 passed` for runtime display-image projection guard tests that exercise step-ref projection behavior.

## Criteria Map

- Display parsing and formatting functions are mapped: satisfied by R173's code map.
- Current display perception formatting produces structured image/media content: satisfied by tests covering data-url display projection and display tool step payload image content.
- History and normal tool-result formatting remain text/manifest-only: satisfied by projection-mode tests and artifact manifest tests.
- Raw base64 is not projected as plain text by display parsing/formatting: satisfied for the Cortex projection scope by shell-media and artifact tests; explicit display image data remains inside image content, not text content.
- Focused Cortex tests pass: satisfied by the recorded pytest runs.

## Execution Map

- T177 was executed as one bounded Cortex-local audit.
- No code changes were made because existing behavior and tests already covered the scoped contract.
- Known gaps were not waived; they are assigned to P189, P190, and P191.

## Stress Test

- The relevant failure modes were:
  - artifact image blob being inlined into display perception: covered by `test_tool_output_v1_display_perception_never_inlines_artifact_image`;
  - shell/base64-like stdout becoming image media: covered by `test_media_like_shell_step_payload_does_not_project_as_display_image`;
  - display projection modes accidentally leaking media into history/current tool result: covered by `test_explicit_projection_modes_control_parsed_display_files`.

## Residual Risk

- Cortex emits internal `_mcp_content`, not final provider API messages. Provider conversion is still open under P190.
- Runtime selection/order semantics are still open under P189.

## Result IDs

- R173
