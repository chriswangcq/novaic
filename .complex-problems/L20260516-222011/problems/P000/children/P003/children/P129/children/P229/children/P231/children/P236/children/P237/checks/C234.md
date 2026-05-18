# Check: runtime shell handoff is compact and durable-payload backed

## Summary

`P237` is solved by `R220`. The runtime shell path has explicit code-level separation between bounded public terminal text and raw durable payload, and focused tests exercise large stdout and media-like/base64-like stdout behavior.

## Evidence

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:167-242` bounds stdout/stderr previews, caps final public text through `tool_text`, and stores raw shell result in `_novaic_durable_payload` with `tool-step-payload.v1`.
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:288-320` routes shell bridge results through `_shell_result_output`.
- `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py:137-171` verifies large output and media-like stdout stay bounded as terminal text and raw output remains only in durable payload.
- `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py:162-210` verifies durable payload persistence while observation preview stays compact.
- Focused tests passed: `19 passed in 0.13s`.

## Criteria Map

- Runtime shell handler/projection code is mapped with file/function pointers: satisfied by `_preview_shell_stream`, `_shell_result_text`, `_shell_result_output`, `_exec_shell`, and `build_save_results_tasks` evidence.
- Evidence shows public shell result text is bounded/terminal-like and raw output is separated as durable payload or artifact metadata: satisfied by code and tests asserting text bounds, truncation markers, no `raw_shell_result` diagnostics, and raw stdout inside durable payload.
- Focused shell projection/runtime tests pass: satisfied by `test_shell_output_contract.py` and `test_runtime_explicit_contracts.py` passing 19 tests.

## Execution Map

- Ticket `T226` was a bounded shell-only audit.
- Execution inspected handler and test code, ran focused tests, and recorded result `R220`.

## Stress Test

The plausible regression is a shell command printing base64-like image data and that text being interpreted as image/history content. `test_shell_media_like_stdout_stays_bounded_terminal_text` covers this class: stdout starts with `/9j/`, stays bounded, does not create `_mcp_content`, and does not include `data:image/`; the raw full output remains in durable payload.

## Residual Risk

Non-blocking for `P237`: direct display/media output uses a separate path and is still covered by `P238`; CLI-by-CLI artifact manifest quality remains under `P230`.

## Result IDs

- `R220`
