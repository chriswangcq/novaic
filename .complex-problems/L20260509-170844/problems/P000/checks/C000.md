# Payload tool schema cutover success check

## Status

success

## Result IDs

- R000

## Criteria Map

- LLM-visible builtin schemas exclude direct payload tools: satisfied by canonical schema import smoke and `novaic-cortex/tests/test_tool_schemas_limits.py::test_payload_tools_are_shell_capabilities_not_llm_schemas`.
- Shell help advertises replacement payload commands: satisfied by `novaic-cortex/tests/test_shell_capability_runtime.py` help and round-trip tests.
- Shell capability can read/search payloads through stable command surface: satisfied by `test_cortex_payload_read_and_search_round_trip_through_shell`.
- Runtime guard tests treat payload executors as schema-cutover compatibility: satisfied by `SHELL_CAPABILITY_SCHEMA_CUTOVER_TOOLS` and runtime tool-path tests.
- Existing compatibility behavior remains tested: satisfied by targeted Runtime handler and shell-output tests.

## Execution Map

- `novaic-cortex/novaic_cortex/sandbox.py`: added `cortex payload` shell command implementation and explicit payload env allowlist.
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`: injects payload interpretation model config only for shell commands that ask for `cortex payload summarize` or `cortex payload qa`.
- `novaic-common/common/tools/llm_builtin.py`: removed direct payload tools from LLM schema and updated shell description.
- `novaic-agent-runtime/task_queue/tool_surface_policy.py`: marks payload direct executors as completed schema cutover tools.
- Common, Cortex, and Runtime tests updated to lock the new boundary.

## Evidence

- Runtime targeted tests: `51 passed`.
- Cortex targeted tests: `16 passed`.
- Common targeted tests: `24 passed`.
- Residual scan shows payload direct names only in the non-LLM payload command-contract module/tests, not in canonical active schema exposure.

## Stress Test

The shell capability test exercises `cortex payload read` and `cortex payload search` through a disposable sandbox and fake Cortex HTTP endpoint. This validates the actual command path, not only the schema list. Runtime shell-output tests also validate payload interpretation env injection without exposing hidden global reads inside the command script.

## Residual Risk

This closes the payload schema cutover, not physical deletion. Direct payload executor code remains intentionally as compatibility until the final cleanup ticket deletes all migrated direct executor branches together.
