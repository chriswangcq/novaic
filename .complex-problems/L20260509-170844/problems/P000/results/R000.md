# Payload tool schema cutover result

## Summary

Completed the payload schema cutover ticket: payload inspection is now advertised through the `cortex payload ...` shell capability instead of direct LLM-visible payload tools, while direct payload executors remain internally available for compatibility and existing handler coverage.

## Done

- Added shell capability commands:
  - `cortex payload read --payload-ref REF`
  - `cortex payload search --payload-ref REF --query TEXT`
  - `cortex payload summarize --payload-ref REF`
  - `cortex payload qa --payload-ref REF --question TEXT`
- Wired payload read/search shell commands to existing Cortex `/v1/payload/read` and `/v1/payload/search` endpoints.
- Wired payload summarize/qa shell commands to existing Cortex interpretation endpoints, with explicit model/factory config supplied by flags or `NOVAIC_PAYLOAD_*` environment.
- Added Runtime shell env injection for payload summarize/qa commands using explicit Business LLM config lookup at the shell boundary.
- Removed `payload_read`, `payload_search`, `payload_summarize`, and `payload_qa` from canonical LLM-facing builtin schemas.
- Updated shell schema guidance to advertise `cortex payload read/search/summarize/qa`.
- Extended `SHELL_CAPABILITY_SCHEMA_CUTOVER_TOOLS` to include the payload tool family.
- Updated Common/Cortex/Runtime tests so payload command contracts remain available but are not LLM-visible tools.

## Verification

- `cd novaic-agent-runtime && python -m pytest tests/test_runtime_tool_path_contract.py tests/test_tool_surface_boundary.py tests/unit/task_queue/test_shell_output_contract.py tests/unit/task_queue/test_environment_tool_handlers.py tests/test_pr48_turn_finalizer.py -q`
  - Passed: `51 passed`
- `cd novaic-cortex && python -m pytest tests/test_tool_schemas_limits.py tests/test_shell_capability_runtime.py -q`
  - Passed: `16 passed`
- `cd novaic-common && python -m pytest tests/test_tool_definitions_contract.py tests/test_environment_tool_schemas.py tests/test_tool_product_semantics_contract.py tests/test_payload_tool_schemas.py tests/test_llm_assembly_contract.py -q`
  - Passed: `24 passed`

## Residual Risk

- Direct payload executors still exist as compatibility code and are still covered by handler-level tests. Physical deletion belongs to a later cleanup ticket after all shell capability cutovers are complete.
- Some pure assembly tests can still feed arbitrary payload-like raw schemas to test assembly behavior, but the canonical active schema list no longer exposes payload tools.
