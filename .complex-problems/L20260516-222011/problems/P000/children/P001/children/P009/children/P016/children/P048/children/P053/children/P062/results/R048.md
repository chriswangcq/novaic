# Base64 Leakage Surface Audit Result

## Summary

Scanned active runtime, Cortex, LLM Factory, and vmuse/device paths for base64/image markers. The relevant surfaces split cleanly into legitimate structured image transport, device-to-blob conversion boundaries, and public text/log/context contracts that need regression guards.

## Done

- Scanned for `/9j/`, `data:image`, `SECRETBASE64`, `base64encoded`, `base64`, `_mcp_content`, `image_url`, `display_files`, `tool-output.v1`, `tool-step-payload.v1`, and `shell_result`.
- Classified legitimate structured image payloads:
  - Runtime display durable payload and multimodal conversion may contain image `data` before provider conversion.
  - Cortex explicit display perception may contain image data only in display-specific projection.
  - LLM Factory provider-native image fields may contain base64 in structured fields.
- Classified device/blob conversion boundaries:
  - `novaic-cortex/novaic_cortex/shell_capabilities.py` decodes device base64 and uploads to Blob, returning `tool-output.v1` artifact manifests.
  - `novaic-mcp-vmuse` still has internal screenshot/file base64 handling as a lower-level device/MCP boundary.
- Classified public-text guard targets:
  - Runtime shell public output must remain bounded `tool-output.v1` text.
  - Cortex shell `tool-step-payload.v1` must project `llm_content`, not `raw.stdout`.
  - LLM Factory logs must redact OpenAI data URLs and Anthropic image source data.

## Verification

- Ran targeted `rg` scans over:
  - `novaic-agent-runtime`
  - `novaic-cortex`
  - `novaic-llm-factory`
  - `novaic-mcp-vmuse`
- Inspected representative high-risk files:
  - `novaic-cortex/novaic_cortex/shell_capabilities.py`
  - `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
  - `novaic-cortex/novaic_cortex/step_result_projection.py`
  - `novaic-llm-factory/factory/contracts.py`

## Known Gaps

- A consolidated active-path guard test should be implemented in `P063`. It should not ban all base64. It should assert public text/log/history boundaries either redact, bound, or explicitly classify base64-bearing structured fields.

## Artifacts

- Scan evidence from `rg` output in execution logs.
- Recommended guard placement:
  - runtime shell/display contract tests,
  - Cortex projection tests,
  - LLM Factory chat snapshot redaction tests.
