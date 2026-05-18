# Factory provider multimodal adapter preservation

## Problem

Audit LLM Factory/provider adapter code to ensure incoming structured image content is sent to the provider API in the correct schema and is not dropped or textified. Request logs should preserve useful observability without misleadingly showing media as plain text payload.

## Success Criteria

- Map factory/provider adapter code for OpenAI-compatible multimodal messages.
- Prove image content is preserved in the provider request schema.
- Prove raw base64 does not appear inside plain text content.
- Prove request/log detail behavior is accurate enough to debug media calls.
- Add or verify focused adapter/log tests.
