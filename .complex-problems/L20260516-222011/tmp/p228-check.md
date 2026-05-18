# Check: explicit Cortex payload inspection APIs satisfy boundary criteria

## Summary

`P228` is solved by `R218`. The result maps the explicit payload API routes, verifies bounded read/search behavior with tests, and separates summarize/qa from automatic context assembly. The known sibling work is correctly scoped outside this problem: write-path/context-assembly boundaries and tool guidance are separate ledger problems.

## Evidence

- `novaic-cortex/novaic_cortex/api.py:1615-2141` contains the payload request models, lookup helpers, read/search endpoints, redaction, bounded interpreter input/output, and summarize/qa endpoints.
- `R218` records the targeted payload API inspection and the command `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_payload_inspection_api.py`.
- The recorded test result is `6 passed in 0.31s`.
- `novaic-cortex/tests/test_payload_inspection_api.py` covers bounded tail reads, bounded search contexts, missing ref handling, missing payload record detail, summarize redaction/input bounds, and QA question/output bounds.

## Criteria Map

- Payload API entrypoints are mapped with file/function pointers: satisfied by the mapped `PayloadReadRequest`, `PayloadSearchRequest`, `PayloadSummarizeRequest`, `PayloadQARequest`, `_payload_text_by_ref`, and `/v1/payload/*` routes in `api.py:1615-2141`.
- Read/search behavior is bounded by explicit mode/limit/query inputs: satisfied by `/v1/payload/read` limit/mode/offset clamping and `/v1/payload/search` query/max/context clamping, plus test coverage recorded in `R218`.
- Summarize/qa behavior is classified as explicit payload interpretation, not default context assembly: satisfied by explicit `/v1/payload/summarize` and `/v1/payload/qa` routes using `_interpret_payload`, while formatted step reads remain projection based.
- Tests verify bounded retrieval behavior: satisfied by `test_payload_inspection_api.py` passing all 6 tests.

## Execution Map

- Ticket `T221` was classified as a bounded one-go audit.
- Execution inspected the API implementation and tests, then ran the targeted pytest file.
- Result `R218` recorded the implementation map, verification command, result, gaps, and artifacts.

## Stress Test

The skeptical failure mode is that a payload API might silently fall back to whole-payload or default-history injection. Evidence argues against that for this problem scope: payload reads require explicit `payload_ref`, use `_payload_slice` with clamped limits, searches cap match count/context size, and summarize/qa call explicit payload interpretation with bounded/redacted input. Default step formatting paths return projections/previews rather than full payload bodies.

## Residual Risk

Residual risk is non-blocking for `P228`: this check does not prove the payload write path, normal context assembly path, or CLI guidance are fully aligned. Those are already represented as sibling problems `P229` and `P230`, so they should be solved there rather than hidden inside this success check.

## Result IDs

- `R218`
