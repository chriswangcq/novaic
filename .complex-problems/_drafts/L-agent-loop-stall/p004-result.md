# Shell internal auth repair result

## Summary

Repaired the shell capability Cortex internal-auth boundary so runtime-injected shell commands can call Cortex internal APIs with `X-Internal-Key`.

## Done

- Added `NOVAIC_CORTEX_INTERNAL_KEY` to runtime shell `capability_env`.
- Added `NOVAIC_CORTEX_INTERNAL_KEY` to Cortex shell capability env allowlist.
- Changed shell capability `_cortex_post` to attach `X-Internal-Key` when the key is present.
- Kept business/device calls on the existing no-internal-key path.
- Added regression coverage for env propagation and generated `agentctl` request headers.

## Verification

- `pytest -q tests/unit/task_queue/test_shell_output_contract.py tests/test_runtime_explicit_contracts.py::test_cortex_bridge_shell_exec_sends_explicit_capability_env` in `novaic-agent-runtime`: `6 passed`.
- `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-logicalfs:/Users/wangchaoqun/new-build-novaic/novaic-sandbox-sdk:/Users/wangchaoqun/new-build-novaic/novaic-sandbox-service:/Users/wangchaoqun/new-build-novaic/novaic-common pytest -q tests/test_shell_capabilities_internal_auth.py` in `novaic-cortex`: `2 passed`.

## Known Gaps

- None for this boundary. The full production stall still requires the step-ref and compensation-context repairs.

## Artifacts

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py`
- `novaic-cortex/novaic_cortex/shell_capabilities.py`
- `novaic-cortex/tests/test_shell_capabilities_internal_auth.py`
