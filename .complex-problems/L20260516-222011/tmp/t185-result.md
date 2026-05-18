# Factory multimodal log detail serialization result

## Summary

Audited Factory multimodal log/detail serialization and added a route-level regression for log detail reads. Request body snapshots preserve message/image structure, redact data-url/base64 payloads, and `get_log` returns the stored body rather than `{}`.

## Done

- Mapped Factory log write path:
  - `novaic-llm-factory/factory/routes/chat_routes.py`
    - `build_chat_log_snapshot(...)` used when creating request logs.
- Mapped log snapshot contract:
  - `novaic-llm-factory/factory/contracts.py`
    - `_redact_message_media_for_log`
    - `_redact_data_url_for_log`
    - `build_chat_log_snapshot`
- Mapped log detail read path:
  - `novaic-llm-factory/factory/routes/log_routes.py`
    - `get_log`
  - `novaic-llm-factory/factory/db.py`
    - `get_log`
- Added `test_log_detail_returns_redacted_multimodal_request_body`.
- The new test writes a redacted multimodal request body, reads it through the route handler, and asserts:
  - body is not `{}`;
  - text content remains visible;
  - `image_url` structure remains visible;
  - raw base64 is absent;
  - redaction metadata includes media type and original char count.

## Verification

```bash
pytest -q \
  novaic-llm-factory/tests/test_log_routes.py \
  novaic-llm-factory/tests/test_chat_routes.py
```

Result: `16 passed in 0.24s`.

## Known Gaps

- Frontend rendering of the returned log body is not judged here. Backend serialization/API behavior is covered.

## Artifacts

- `novaic-llm-factory/factory/contracts.py`
- `novaic-llm-factory/factory/routes/chat_routes.py`
- `novaic-llm-factory/factory/routes/log_routes.py`
- `novaic-llm-factory/tests/test_log_routes.py`
- `novaic-llm-factory/tests/test_chat_routes.py`
