# Provider media adapter conversion

## Problem

Audit the final provider request conversion for current display media. Internal display/media content must become provider-consumable image input according to the target LLM API schema, not a text string containing blob refs or base64.

## Success Criteria

- Map provider adapter code that converts internal multimodal content to final API request messages.
- Prove current display blob input becomes provider image/media content in the request body.
- Prove no raw base64 text is present in provider text fields.
- Fix or create follow-up work for any provider adapter that drops or textifies current display media.
