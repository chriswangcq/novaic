# Runtime-to-factory multimodal request preservation

## Problem

Audit the runtime LLM transport boundary to ensure prepared messages containing provider-shaped image content are sent to LLM Factory without being stringified, flattened, or converted to plain text.

## Success Criteria

- Map runtime LLM transport/client request builder.
- Prove prepared OpenAI image content reaches the factory request body as structured content.
- Prove raw base64 is not moved into a plain text field by runtime serialization.
- Add or verify focused tests for runtime-to-factory multimodal request payloads.

