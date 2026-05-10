# Audio QA tool schema cutover result

## Summary

Completed the audio QA schema cutover: `audio_qa` is no longer an LLM-visible builtin schema, and audio transcription/QA is available through `agentctl media audio-qa` in the shell capability surface.

## Done

- Added `agentctl media audio-qa --file-url blob://namespace/id`.
- Added prompt support through `--prompt` and `--prompt-file`.
- Implemented Blob fetch with explicit `NOVAIC_BLOB_SERVICE_URL` and `NOVAIC_USER_ID`.
- Implemented audio model config lookup through Business `/internal/config/llm/agent/{agent_id}/audio`.
- Implemented Factory `/v1/chat/completions` call with `input_audio` payload.
- Removed `audio_qa` from canonical LLM-facing builtin schemas and Common active multimodal metadata.
- Added `audio_qa` to completed schema-cutover compatibility policy.
- Updated shell help/schema tests and product semantics tests.

## Verification

- `cd novaic-agent-runtime && python -m pytest tests/test_runtime_tool_path_contract.py tests/test_tool_surface_boundary.py tests/unit/task_queue/test_shell_output_contract.py tests/unit/task_queue/test_device_tool_handlers.py -q`
  - Passed: `19 passed`
- `cd novaic-cortex && python -m pytest tests/test_tool_schemas_limits.py tests/test_shell_capability_runtime.py -q`
  - Passed: `20 passed`
- `cd novaic-common && python -m pytest tests/test_tool_definitions_contract.py tests/test_tool_product_semantics_contract.py tests/test_payload_tool_schemas.py -q`
  - Passed: `11 passed`

## Residual Risk

- Direct `audio_qa` executor remains internally available for compatibility until final physical cleanup.
