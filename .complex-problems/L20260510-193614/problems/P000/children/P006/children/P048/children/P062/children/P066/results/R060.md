# Phase 5D.2b execution result

## Summary

Executed the step formatting and sandbox contract guard ticket. The public `steps_read_formatted` API is covered by explicit `projection` validation, low-level `include_display` remains confined to internal step result rendering helpers, and sandbox execution rejects leaked `novaic-cortex-sandbox-*` backing paths with stable `/cortex/ro` and `/cortex/rw` guidance.

## Done

- Inspected the public formatted-step API tests in `novaic-cortex/tests/test_context_event_api_steps_write.py`.
- Inspected tool-output projection tests in `novaic-cortex/tests/test_tool_output_projection.py`, `novaic-cortex/tests/test_step_result_projection.py`, and `novaic-cortex/tests/test_resolve_for_llm.py`.
- Inspected sandbox contract tests in `novaic-cortex/tests/test_tool_schemas_limits.py`, `novaic-cortex/tests/test_sandbox_requires_mount_namespace.py`, and `novaic-cortex/tests/test_sandboxd_wiring.py`.
- Confirmed `novaic-cortex/novaic_cortex/sandbox.py` rejects `novaic-cortex-sandbox-*` commands before sandboxd execution and points callers at `/cortex/ro`, `/cortex/rw`, `$RO`, and `$RW`.
- Verified the target guard suite with explicit package boundaries.

## Verification

- Ran:
  `PYTHONPATH="novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk" pytest -q novaic-cortex/tests/test_context_event_api_steps_write.py novaic-cortex/tests/test_tool_output_projection.py novaic-cortex/tests/test_step_result_projection.py novaic-cortex/tests/test_resolve_for_llm.py novaic-cortex/tests/test_tool_schemas_limits.py novaic-cortex/tests/test_sandbox_requires_mount_namespace.py novaic-cortex/tests/test_sandboxd_wiring.py`
- Result: `42 passed in 0.43s`.
- Static evidence:
  - `test_steps_read_formatted_rejects_unknown_projection` asserts `unsupported_step_projection`.
  - `test_explicit_projection_modes_control_parsed_display_files` proves explicit `history`, `current_tool_result`, and `display_perception` modes have distinct display behavior.
  - `test_shell_schema_names_safety_boundary` asserts the shell schema advertises stable Cortex paths and warns against `novaic-cortex-sandbox-*`.
  - `test_shell_rejects_ephemeral_cortex_backing_paths_before_execution` asserts leaked temp backing paths are rejected before execution and do not fall through to the missing-sandboxd path.

## Known Gaps

None for this bounded ticket. Broader lock/fallback boundary coverage remains in sibling problem `P067`.

## Artifacts

- `novaic-cortex/tests/test_sandbox_requires_mount_namespace.py`
- `novaic-cortex/tests/test_context_event_api_steps_write.py`
- `novaic-cortex/tests/test_tool_output_projection.py`
- `novaic-cortex/tests/test_step_result_projection.py`
- `novaic-cortex/tests/test_resolve_for_llm.py`
- `novaic-cortex/tests/test_tool_schemas_limits.py`
- `novaic-cortex/tests/test_sandboxd_wiring.py`
