# Final projection static branch audit result

## Summary

Completed final static projection audit. No active `resolve_for_llm` references remain. Remaining active media/projection branches are classified, and the Google/Gemini provider conversion gap is confirmed for P217.

## Static Checks

- `rg -n "resolve_for_llm" novaic-cortex/novaic_cortex novaic-cortex/tests novaic-agent-runtime novaic-llm-factory novaic-common -S || true`
  - Result: no output.
- Projection/media keyword audit across active Cortex/runtime/factory production and projection tests.

## Classified Active Branches

- Cortex `step_result_projection.py`
  - `tool-output.v1` artifact manifest projection: intentional.
  - `_mcp_content` image parsing into `display_files`: intentional only for explicit display perception.
  - Unknown dict fallback: intentional bounded diagnostic text.
  - No nested `result` unwrapping remains.
- Runtime
  - `task_queue/utils/multimodal.py`: intentional display-perception-only conversion.
  - `task_queue/handlers/tool_handlers.py`: intentional public placeholder + durable payload split for display; intentional bounded shell terminal text.
  - `task_queue/utils/step_result_client.py`: intentional projection routing (`display_perception` only for current display tool calls).
- Factory
  - OpenAI/Anthropic multimodal handling and log redaction tests are active/intentional.
  - Google/Gemini provider `_convert_messages` still stringifies non-string user content and needs P217 fix.

## Follow-up Required

P217 must fix and test Google/Gemini multimodal conversion. No additional production stale helper/test residue was found in active code.

## Code Changes

None. This was a static audit.
