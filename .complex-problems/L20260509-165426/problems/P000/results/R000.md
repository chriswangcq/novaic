# agentctl IM commands implemented

## Summary

Implemented real `agentctl im` shell commands in the sandbox-generated command substrate. The commands can now call Environment IM endpoints and Cortex meta endpoints from inside shell.

## Done

- Extended `agentctl --help` with IM command usage.
- Implemented:
  - `agentctl im read`
  - `agentctl im reply`
  - `agentctl im send`
  - `agentctl im history`
  - `agentctl im search`
  - `agentctl im context`
- `agentctl im read` marks observed message ids in Cortex meta.
- `agentctl im reply` enforces read-before-reply from Cortex meta.
- `agentctl im reply` increments the `im_reply` Cortex counter and enforces `NOVAIC_MAX_USER_REPLIES_PER_SESSION`.
- `agentctl im reply/send` support `--message-file`.
- Added a sandbox subprocess integration test using a local fake HTTP server for Business/Cortex endpoints.

## Verification

- Ran `python -m pytest tests/test_shell_capability_runtime.py -q` in `novaic-cortex`.
- Result: `4 passed`.
- Ran `python -m pytest tests/test_shell_capability_runtime.py tests/test_sandbox_sync.py tests/test_sandbox_limits.py -q`.
- Result: `15 passed`.
- Ran `python -m pytest tests/unit/task_queue/test_shell_output_contract.py tests/test_runtime_explicit_contracts.py tests/test_pr71_no_tool_retry_context_cleanup.py -q` in `novaic-agent-runtime`.
- Result: `23 passed`.

## Residual Risk

- Direct LLM-facing IM tools still exist. A separate cutover/deletion ticket must remove them from the visible schema and then delete or quarantine the old direct executor surface.
