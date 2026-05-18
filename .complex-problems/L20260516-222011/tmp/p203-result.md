# Runtime and factory projection branch inventory parent result

## Summary

Completed the runtime/factory inventory split. Runtime projection boundaries are active and mostly clean; factory/log boundaries are active but revealed one provider adapter gap: Google/Gemini does not preserve multimodal `image_url` content.

## Child Results

- `R186` / `P205`: Runtime projection branch inventory.
- `R187` / `P206`: Factory/provider/log projection branch inventory.

## Consolidated Findings

- Active runtime contract:
  - Cortex step refs resolve through explicit projection modes.
  - Historical/generic tool results remain text-only.
  - Only current `display_perception` messages can become provider-native image messages.
  - Shell output is bounded terminal text with durable raw payload stored separately.
- Active factory/log contract:
  - Runtime factory client preserves structured `messages`.
  - OpenAI provider preserves structured `image_url` content.
  - Anthropic provider converts `image_url` data URLs to native image source blocks.
  - Factory log snapshots redact base64 but preserve structured shape.
- Cleanup/fix candidate:
  - Google/Gemini provider currently stringifies list content and should be fixed in production cleanup.

## Code Changes

None. This parent ticket summarized read-only inventory child results.
