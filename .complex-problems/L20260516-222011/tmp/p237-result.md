# Result: runtime shell handoff projection boundary audited

## Summary

Runtime shell handoff is compact and durable-payload backed. The shell executor converts raw shell results into `tool-output.v1` public text bounded by terminal-style preview limits, stores the full raw shell result under `_novaic_durable_payload`, and `react_actions` persists durable payload while exposing only public compact observation content.

## Done

- Mapped shell result projection in `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`.
- Verified stream preview limits: stdout/stderr previews are capped, files_changed are capped, and final public text is passed through `tool_text` with a text limit.
- Verified `_shell_result_output` attaches `tool-step-payload.v1` durable payload containing full raw stdout/stderr/files_changed while public content stays compact.
- Verified `_exec_shell` normalizes shell bridge output and returns `_shell_result_output`.
- Verified `build_save_results_tasks` persists durable payload and keeps observation summary/preview compact.
- Ran focused runtime shell tests.

## Verification

- Code evidence: `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:167-242` defines shell preview limits, public `tool-output.v1` text, diagnostics, and durable raw payload.
- Code evidence: `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:288-320` routes shell bridge results through `_shell_result_output`.
- Code evidence: `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py:162-210` verifies durable payload is persisted while observation preview omits repeated raw output.
- Test evidence: `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py:52-171` covers explicit output contract, capability env, nonzero exits, large output truncation, and media-like stdout bounded as terminal text.
- Test command: `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`.
- Test result: `19 passed in 0.13s`.

## Known Gaps

- This result covers runtime shell handoff only. Direct display/media handoff is handled by sibling problem `P238`.
- CLI-by-CLI output contract coverage is intentionally left to `P230`.

## Artifacts

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py`
- `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`
