# stale artifact namespace fixtures cleaned

## Summary

Replaced stale `blob://device-screenshot/...` test fixtures with `blob://runtime-artifact/...` in CLI/tool-output contract tests.

## Done

- Updated `novaic-agent-runtime/tests/unit/task_queue/test_tool_output_contract.py`.
- Updated `novaic-cortex/tests/test_tool_output_projection.py`.
- Verified `rg -n "device-screenshot" novaic-cortex/tests novaic-agent-runtime/tests/unit/task_queue` returns no matches.

## Verification

- Ran `PYTHONPATH=../novaic-common:../novaic-logicalfs:../novaic-sandbox-sdk:. pytest -q tests/test_tool_output_projection.py tests/test_shell_capabilities_blob_contract.py` in `novaic-cortex`.
- Result: `7 passed in 1.22s`.
- Ran `PYTHONPATH=../novaic-common:../novaic-cortex:../novaic-logicalfs:../novaic-sandbox-sdk:. pytest -q tests/unit/task_queue/test_tool_output_contract.py tests/unit/task_queue/test_shell_output_contract.py` in `novaic-agent-runtime`.
- Result: `12 passed in 0.09s`.

## Known Gaps

- None for stale `device-screenshot` fixtures.

## Artifacts

- `novaic-agent-runtime/tests/unit/task_queue/test_tool_output_contract.py`
- `novaic-cortex/tests/test_tool_output_projection.py`
