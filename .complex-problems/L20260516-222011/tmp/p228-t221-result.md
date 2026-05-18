# Result: explicit Cortex payload inspection APIs audited

## Summary

Audited the explicit Cortex payload inspection APIs for `payload_read`, `payload_search`, `payload_summarize`, and `payload_qa`. The active implementation requires explicit `scope_id` and `payload_ref`, resolves the referenced durable step payload, bounds all returned slices/search contexts/interpreter inputs, redacts sensitive-looking values before interpretation, and keeps summarize/qa as explicit interpretation actions rather than implicit context assembly.

## Done

- Mapped the request models in `novaic-cortex/novaic_cortex/api.py`: `PayloadReadRequest`, `PayloadSearchRequest`, `PayloadSummarizeRequest`, and `PayloadQARequest`.
- Mapped the payload lookup path through `_find_step_by_payload_ref`, `_read_step_payload`, and `_payload_text_by_ref`.
- Verified `/v1/payload/read` clamps limit and offset behavior and supports bounded `preview`, `head`, `tail`, and `range` modes.
- Verified `/v1/payload/search` clamps `max_matches` and `context_chars`, requires a query, and returns bounded match contexts.
- Verified `/v1/payload/summarize` and `/v1/payload/qa` use explicit factory interpretation calls, bounded input/output sizes, and redaction before model submission.
- Confirmed formatted step reads remain projection based through `/v1/steps/read_formatted` and `/v1/steps/read_preview`; full payload inspection stays under explicit payload APIs.

## Verification

- Inspected `novaic-cortex/novaic_cortex/api.py:1615-2141` for request models, lookup, bounds, redaction, and endpoints.
- Ran `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_payload_inspection_api.py`.
- Test result: `6 passed in 0.31s`.
- Existing tests cover bounded tail reads, bounded search contexts, missing refs, missing payload record detail, summarize bounded/redacted factory input, and QA question/output bounds.

## Known Gaps

- No gap found in the explicit payload inspection API boundary itself.
- Payload write boundaries, normal context assembly behavior, CLI guidance, and schema exposure are intentionally left to sibling problems `P229` and `P230`.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_payload_inspection_api.py`
