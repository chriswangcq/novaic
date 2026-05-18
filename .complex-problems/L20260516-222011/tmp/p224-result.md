# Active projection branch classification result

## Summary

Classified active projection branch sites across Cortex, runtime, and factory. No unclassified stale branch was found; remaining branches are tied to current shell/display/history/provider/logging contracts.

## Done

- Searched Cortex projection code/tests for `_mcp_content`, `display_perception`, `tool-output.v1`, artifacts, image/data-url handling, and unknown fallback markers.
- Searched runtime task-queue context and tool handling for display-only multimodal projection and shell/display public-output wrapping.
- Searched factory provider/log projection surfaces for `image_url`, `inlineData`, base64 handling, and redaction.
- Inspected line-numbered source slices for the active branch sites.

## Verification

- `novaic-cortex/novaic_cortex/step_result_projection.py:56-87`: `tool-output.v1` manifests are parsed as terminal text plus artifact/event receipts. Intentional shell/CLI contract.
- `novaic-cortex/novaic_cortex/step_result_projection.py:142-179`: MCP content arrays are parsed into text and display files. Intentional compatibility for display perception and resource display contracts; current/history formatting decides whether media can enter LLM.
- `novaic-cortex/novaic_cortex/step_result_projection.py:185-199`: unknown dict fallback is bounded diagnostic text. Intentional safety net to prevent unexpected payload flooding context.
- `novaic-cortex/novaic_cortex/step_result_projection.py:202-279`: `include_display=False` for history/current non-display outputs and `include_display=True` only for explicit display perception. Intentional projection boundary.
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:84-115`: generic tool outputs are wrapped into `tool-output.v1`. Intentional terminal-style public contract.
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:118-164`: display public output strips image bytes while durable payload preserves LLM content. Intentional split between public history and current perception.
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:178-242`: shell output is length-bounded text with raw data in durable payload. Intentional shell-as-terminal contract.
- `novaic-agent-runtime/task_queue/utils/step_result_client.py:126-139`: only current-round `display` tool messages get `display_perception`; historical or non-display tools get text/manifest projections. Intentional current-turn media gate.
- `novaic-agent-runtime/task_queue/utils/context.py:203-249`: only `display_perception` tool results are converted into provider image messages; other tools remain text receipts. Intentional anti-historical-image-injection guard.
- `novaic-agent-runtime/task_queue/utils/multimodal.py:12-131`: converts display `_mcp_content` image data into provider-native content and replaces tool-result image data with placeholders. Intentional current display perception bridge.
- `novaic-llm-factory/factory/providers.py:201-252`: Anthropic provider converts data URL image content into native base64 image blocks. Intentional provider adapter behavior, covered by tests.
- `novaic-llm-factory/factory/providers.py:360-422`: Google/Gemini provider converts data URL image content into `inlineData`; non-data URLs become text placeholders. Intentional provider adapter behavior, covered by new regression test.
- `novaic-llm-factory/factory/contracts.py:80-147`: log snapshots redact data URL and provider-native image base64. Intentional observability/privacy contract.

## Known Gaps

- No stale branch found in the audited projection surface.
- Non-blocking nuance: runtime currently keeps display-derived user image messages before a following Active Skill Stack system message, and there is an explicit test for that ordering. This is intentional current behavior, not an unclassified branch.

## Artifacts

- `novaic-cortex/novaic_cortex/step_result_projection.py`
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- `novaic-agent-runtime/task_queue/utils/step_result_client.py`
- `novaic-agent-runtime/task_queue/utils/context.py`
- `novaic-agent-runtime/task_queue/utils/multimodal.py`
- `novaic-llm-factory/factory/providers.py`
- `novaic-llm-factory/factory/contracts.py`
