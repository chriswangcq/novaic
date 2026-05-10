# Audio QA tool schema cutover success check

## Status

success

## Result IDs

- R000

## Criteria Map

- LLM schemas exclude `audio_qa`: satisfied by Cortex schema guard tests and Common product semantics tests.
- Shell help advertises replacement command: satisfied by shell schema/help tests.
- Shell command fetches Blob, resolves audio model config, calls Factory, and returns JSON: satisfied by `test_agentctl_media_audio_qa_round_trip_through_shell`.
- Runtime guards classify direct executor as schema-cutover compatibility: satisfied by Runtime tool-surface policy tests.

## Execution Map

- `novaic-cortex/novaic_cortex/sandbox.py`: implemented `agentctl media audio-qa`.
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`: exposes `NOVAIC_BLOB_SERVICE_URL` to shell capabilities.
- `novaic-common/common/tools/llm_builtin.py`: removed direct `audio_qa` schema and advertised shell command.
- `novaic-common/common/tools/definitions.py`: removed active multimodal metadata for `audio_qa`.
- `novaic-agent-runtime/task_queue/tool_surface_policy.py`: classifies `audio_qa` as completed schema cutover.

## Evidence

- Runtime targeted tests: `19 passed`.
- Cortex targeted tests: `20 passed`.
- Common targeted tests: `11 passed`.

## Stress Test

The shell test uses a fake Blob endpoint, fake Business audio model config, and fake Factory chat completions endpoint. It validates all external hops and the produced Factory payload, including audio base64 format, tenant header, x_factory metadata, and final JSON response.

## Residual Risk

The direct Runtime `audio_qa` executor still exists for compatibility and final deletion. This check validates schema cutover, not physical old-code deletion.
