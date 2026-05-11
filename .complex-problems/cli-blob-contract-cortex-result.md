# cortex payload Blob contract audit completed

## Summary

Audited generated `cortex payload` CLI output paths. No raw artifact stdout violation was found. The commands are bounded text inspection or bounded interpretation calls.

## Done

- Inspected `novaic-cortex/novaic_cortex/shell_capabilities.py` `_cortex_payload`.
- Confirmed `payload read` sends `limit` through `_flag_int(..., 2000, 1, 8000)`.
- Confirmed `payload search` caps `max_matches` at 20 and `context_chars` at 500.
- Confirmed `payload summarize` and `payload qa` cap model input/output sizes (`max_input_chars` 1000..20000, `max_output_chars` 200..4000).
- Confirmed no `cortex payload` path decodes or prints base64 artifact bytes.

## Verification

- Ran `PYTHONPATH=../novaic-common:../novaic-logicalfs:../novaic-sandbox-sdk:. pytest -q tests/test_blob_payload_client.py tests/test_tool_schemas_limits.py tests/test_context_event_api_steps_write.py tests/test_step_index_outcome.py` in `novaic-cortex`.
- Result: `38 passed in 0.45s`.

## Known Gaps

- No P006-blocking gaps found.
- This audit intentionally treats bounded payload text slices as allowed CLI output.

## Artifacts

- Audit evidence: `novaic-cortex/novaic_cortex/shell_capabilities.py` `_cortex_payload` implementation.
