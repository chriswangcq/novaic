# Child Problem: provider adapters receive image payloads through the right contract

## Problem

Even if runtime context assembly creates image blocks, provider adapters may still flatten or redact them incorrectly. The provider-facing contract must carry images in the format expected by the active LLM API while keeping logs/redaction safe.

## Success Criteria

- Provider adapters accept the runtime image representation without converting it to plain text.
- LLM Factory logs redact image bytes while preserving the fact that an image input was sent.
- Focused tests cover provider request redaction and image payload preservation.
