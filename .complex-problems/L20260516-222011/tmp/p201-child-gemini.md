# Fix Google/Gemini multimodal provider conversion

## Problem

Inventory found that Google/Gemini provider handling does not preserve/convert list multimodal message content, so display image perception can silently degrade or stringify.

## Success Criteria

- Google/Gemini provider converts text + image content into a native request shape.
- Provider tests prove base64 image data is not placed into text parts.
- Existing OpenAI/Anthropic behavior remains intact.
