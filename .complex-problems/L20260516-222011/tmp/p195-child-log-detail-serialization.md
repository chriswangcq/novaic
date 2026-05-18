# Factory multimodal log detail serialization

## Problem

Audit Factory log/detail serialization for multimodal calls. The log UI/API should show useful request/response structure without collapsing calls to `{}` or presenting media as misleading plain text.

## Success Criteria

- Locate Factory logging/detail API and persistence schema for request/response bodies.
- Prove multimodal request details retain enough structured information to debug calls.
- Prove large/base64 media is redacted or represented safely, not rendered as a giant text blob.
- Add or verify focused log/detail tests.
