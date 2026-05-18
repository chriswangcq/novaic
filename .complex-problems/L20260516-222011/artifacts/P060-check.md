# Cortex Shell Projection Check

## Summary

Successful. Cortex step projection preserves shell terminal semantics by projecting the bounded `llm_content` field and not durable raw shell stdout.

## Evidence

- `R045` inspected `novaic-cortex/novaic_cortex/step_result_projection.py`.
- `parse_tool_result()` routes `tool-step-payload.v1` to `llm_content`.
- `test_tool_step_payload_v1_projects_llm_content_not_raw_shell_payload` covers a 10,000-character raw shell stdout and asserts it is absent from parsed text.
- Focused Cortex tests passed: `14 passed`.

## Criteria Map

- Cortex history projection does not inline `durable_payload.raw.stdout`:
  - Satisfied by code path and exact test.
- Shell step payloads are projected as bounded terminal text or pointers:
  - Satisfied by `tool-output.v1` text/artifact/event projection.
- Focused tests cover shell step projection:
  - Satisfied by `tests/test_tool_output_projection.py` and `tests/test_step_result_projection.py`.

## Execution Map

- `T051` audited Cortex projection and ran focused tests.
- No production patch was needed.

## Stress Test

- The test includes raw shell stdout of `x * 10000` and proves parsed text only contains the short preview from `llm_content`.

## Residual Risk

- Low for Cortex shell projection. P061 still needs explicit media-like/base64 regression coverage across the shell/context boundary.

## Result IDs

- R045
