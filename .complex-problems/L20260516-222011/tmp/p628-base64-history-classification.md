# P628 Base64 Public-History Classification

## Private Wire / Durable Payload

- `novaic-sandbox-sdk/sandbox_sdk/contracts.py` uses `stdout_b64`/`stderr_b64` for sandboxd JSON wire bytes. This is private service wire handling.
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py::_shell_result_output` keeps raw shell stdout/stderr in `durable_payload.raw`, while public `llm_content` is bounded terminal text.
- `novaic-cortex/novaic_cortex/shell_capabilities.py` decodes device base64 responses and uploads files to Blob, then prints a tool-output artifact manifest with `blob://runtime-artifact/...`, not raw base64.

## Public History / Tool Text

- Runtime display wrapper replaces image bytes in public tool content with placeholders and stores `image_ref`/BlobRef in durable `llm_content`.
- Historical replay reads formatted step projections and must ignore inline historical tool content; tests assert raw `YWJjMTIz` does not re-enter shell/display history.
- Shell stdout remains terminal-like bounded text. If a command prints JPEG-like base64, the public text is truncated and diagnostics record lengths; raw stdout remains only in durable payload for RO inspection.
- Frontend monitor detail redacts raw `data:image/*;base64` and long binary-looking base64 details.

## Current Multimodal Perception

- Current `display` perception can create a provider multimodal image input from Blob content. Tests represent that as an OpenAI-compatible `image_url` data URL for the current call. This is not historical tool text and is intentionally absent from replayed history.

## Compatibility / Test Fixtures

- `step_result_projection.py` still supports legacy MCP `image` items with inline data/data URLs for parsing old or direct display payload shapes. Guard tests ensure current artifact/BlobRef paths project as manifest/image_ref instead of raw shell payload.
- Test files contain sample base64 strings to assert non-leak behavior.

## Risky Residue

No active raw base64 public-history leak found in the scanned surfaces. Compatibility parsers remain, but current shell/display history projection is guarded by tests.
