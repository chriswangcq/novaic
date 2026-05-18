# P197 Check: factory multimodal log detail serialization

## Summary

Success. R179 solves P197 for backend serialization/API behavior: multimodal request snapshots preserve useful structure, redact raw image bytes, and detail reads return the populated body rather than `{}`.

## Evidence

- Chat route writes request bodies through `build_chat_log_snapshot`.
- Contract redaction handles OpenAI `image_url` data URLs and Anthropic image source base64.
- Log detail route returns `db.get_log(log_id)` with request/response bodies.
- New route-level test proves redacted multimodal request body survives through DB and `get_log`.

## Criteria Map

- Factory log snapshot and detail route code paths are mapped: satisfied by R179.
- Multimodal request logs preserve structure and redact image bytes: satisfied by helper tests and new detail test.
- Log detail APIs return request/response bodies rather than empty `{}`: satisfied by existing `test_get_log_fetches_full_body_by_id` and new multimodal detail test.
- Focused log/detail tests pass: `16 passed in 0.24s`.

## Execution Map

- T185 was executed as one backend log/detail serialization audit.
- One regression test was added because helper-level redaction coverage alone did not prove detail-route behavior.

## Stress Test

- The new test uses a data-url JPEG with raw `/9j/SECRETBASE64`, then asserts the route response includes `image_url` structure and redaction metadata while excluding raw base64.

## Residual Risk

- The frontend log modal rendering is outside this backend ticket. If the UI still displays `{}`, that should become a frontend-specific follow-up.

## Result IDs

- R179
