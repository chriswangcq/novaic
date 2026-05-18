# Factory/provider/log projection branch inventory

## Problem

Factory and provider/log layers should preserve structured multimodal request content while redacting large/base64 payloads in logs. We need to classify these branches separately from runtime.

## Success Criteria

- Inventory factory client request construction, provider adapter multimodal conversion, and log detail redaction/rendering.
- Classify suspicious branches as active, compatibility, defensive, or stale.
- Identify cleanup candidates with file/line evidence.
- Do not edit code.
