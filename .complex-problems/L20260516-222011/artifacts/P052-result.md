# Shell Observations Terminal-Shaped Result

## Summary

Closed the shell observation contract across runtime, Cortex projection, and regression coverage. Shell remains a bounded terminal-text tool; complete raw stdout/stderr stays in durable payload/RO records and is not reclassified as display/image content.

## Done

- Closed `P059`: runtime shell wrapper has explicit public stdout/stderr bounds and durable raw retention.
- Closed `P060`: Cortex step projection reads `tool-step-payload.v1.llm_content`, not `raw.stdout`, for normal history.
- Closed `P061`: added media-like `/9j/` stdout regression tests in runtime and Cortex.

## Verification

- Runtime shell contract tests: `12 passed` for P059, plus `6 passed` after P061 changes.
- Cortex projection tests: `14 passed` for P060, plus `15 passed` after P061 changes.

## Known Gaps

- No known blocking gap for this parent ticket.

## Artifacts

- Child result/check evidence:
  - `P059`: `R044`, `C056`
  - `P060`: `R045`, `C057`
  - `P061`: `R046`, `C058`
- Code/test areas:
  - `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
  - `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py`
  - `novaic-cortex/novaic_cortex/step_result_projection.py`
  - `novaic-cortex/tests/test_tool_output_projection.py`
