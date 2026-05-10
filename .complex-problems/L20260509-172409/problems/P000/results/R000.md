# Device tool shell cutover result

## Summary

Completed the dynamic device tool schema cutover for the current bounded ticket. Device interaction remains available from the shell through `devicectl`, while LLM-facing tool schemas no longer fetch or merge mounted device tools during `cortex.prepare_llm_context`.

## Done

- Added `devicectl` as a Cortex sandbox capability command and wired the capability dispatcher.
- Implemented the `devicectl hd` command surface for screenshot, shell-exec, mouse, keyboard, clipboard, and file proxy operations.
- Passed `NOVAIC_DEVICE_URL` through the Runtime shell capability environment boundary.
- Removed mounted device schema fetching/merging from LLM context preparation.
- Marked all `hd_*` device tools as schema-cutover shell capability tools in the runtime tool surface policy.
- Updated shell schema descriptions and guardrail tests to include `devicectl`.
- Added a shell round-trip test proving `devicectl hd shell-exec` posts to Device service with explicit JSON payload.
- Updated context-prepare smoke tests so Business mounted-device schema fetches now fail the test if accidentally reintroduced.

## Evidence

- `cd novaic-agent-runtime && python -m pytest tests/test_pr85_llm_context_smoke_guardrails.py tests/test_runtime_tool_path_contract.py tests/test_tool_surface_boundary.py tests/unit/task_queue/test_device_tool_handlers.py tests/unit/task_queue/test_shell_output_contract.py -q`
  - Result: `26 passed`
- `cd novaic-cortex && python -m pytest tests/test_tool_schemas_limits.py tests/test_shell_capability_runtime.py -q`
  - Result: `21 passed`
- `cd novaic-common && python -m pytest tests/test_tool_definitions_contract.py tests/test_tool_product_semantics_contract.py tests/test_payload_tool_schemas.py -q`
  - Result: `11 passed`

## Residual Risk

- Runtime still keeps direct `hd_*` executors as compatibility executors; they are no longer LLM-visible after this cutover. Physical deletion belongs to the broader old-code cleanup phase, not this schema-cutover ticket.
