# Factory log redaction and detail large-output sweep

## Problem
Audit LLM factory request/response logging and log-detail APIs for redaction, large multimodal request bodies, and raw provider payload exposure.

## Success Criteria
- Factory log storage/detail paths are cited and classified.
- Media/base64 payloads are redacted in persisted/displayed logs.
- Focused log tests pass.
