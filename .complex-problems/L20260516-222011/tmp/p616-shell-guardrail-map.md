# P616 Shell Output Guardrail Map

## Invariant Coverage

- Bounded shell terminal text / truncation: `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py`, `novaic-cortex/tests/test_runtime.py::test_tool_read_truncates_per_micro_max_tool_output_chars`, and P615 read-model tests.
- Artifact manifest instead of raw screenshot/file bytes: `novaic-cortex/tests/test_shell_capabilities_blob_contract.py` and `novaic-cortex/tests/test_tool_output_projection.py`.
- No historical image injection: `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py` and `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py` display projection tests.
- Display current-turn perception only: `novaic-cortex/tests/test_tool_output_projection.py`, `novaic-cortex/tests/test_step_result_projection.py`, and runtime `test_pr71_no_tool_retry_context_cleanup.py` image_ref resolution tests.
- Monitor/UI previews: P603/P604/P612 frontend/backend tests cover monitor preview redaction and bounded display.

## Missing Coverage

- No blocking gap found. The tests are distributed across PR-named files, but their invariants are clear and focused.
