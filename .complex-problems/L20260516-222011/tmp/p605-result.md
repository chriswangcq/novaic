# Exact backend preview boundary evidence result

## Summary

Collected exact line-numbered backend evidence and focused test output for the Agent Monitor/progress preview payload boundary. The evidence shows monitor/progress preview surfaces use bounded previews, payload references, artifact flags, and schema text fields; raw image/base64 production found in the targeted scan belongs to shell/device blob wrapping or explicit display-perception LLM image resolution, not Agent Monitor progress payloads.

## Done

- Captured exact `nl -ba` slices for:
  - Cortex `/v1/steps/read_preview`.
  - Cortex payload slicing, read/search, summarize, and QA APIs.
  - Cortex `Workspace.write_step` payload externalization, `payload_ref`, and `has_artifacts` indexing.
  - Cortex text preview formatting.
  - Business Agent Monitor schema/progress projection fields.
  - Runtime activity projection monitor path fields.
  - Runtime display image-ref resolution path and its explicit display-perception projection boundary.
  - Display tool handler image-ref manifest creation.
- Ran a targeted raw bytes risk scan across `novaic-agent-runtime`, `novaic-business`, and `novaic-cortex`, excluding tests.
- Ran focused pytest coverage for payload externalization, payload read/search/summarize/QA, and Agent Monitor activity timeline boundary.

## Verification

- Focused tests passed:
  - `novaic-cortex/tests/test_step_index_outcome.py::test_write_step_externalizes_payload_and_indexes_payload_ref`
  - `novaic-cortex/tests/test_step_index_outcome.py::test_write_step_externalizes_large_payload_to_blob_ref`
  - `novaic-cortex/tests/test_payload_inspection_api.py::test_payload_read_returns_bounded_tail_slice`
  - `novaic-cortex/tests/test_payload_inspection_api.py::test_payload_search_returns_bounded_match_contexts`
  - `novaic-cortex/tests/test_payload_inspection_api.py::test_payload_summarize_uses_redacted_bounded_factory_input`
  - `novaic-cortex/tests/test_payload_inspection_api.py::test_payload_qa_requires_question_and_bounds_output`
  - `novaic-business/tests/test_pr193_no_activity_timeline_action.py`
- Test output: `8 passed in 0.35s`.
- Raw bytes risk scan found base64/image byte production outside tests only in these expected/non-monitor roles:
  - `novaic-cortex/novaic_cortex/shell_capabilities.py`: decodes device screenshot/file base64, stores BlobRef/artifact manifest, and explicitly removes `screenshot` from `device_result`.
  - `novaic-agent-runtime/task_queue/utils/step_result_client.py`: resolves `image_ref` into provider-native image data only for `display_perception` LLM projection.
  - `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`: display handler returns `image_ref` manifest; native display fallback base64 is isolated to tool/display result handling, not monitor progress.
- No backend Agent Monitor/progress event path was found carrying raw unredacted image bytes or screenshot base64.

## Known Gaps

- This is a focused boundary audit, not a full end-to-end browser/monitor UI render test.
- The scan confirms current code paths, but future monitor event fields could regress unless the existing tests remain in CI and new monitor payload features reuse the same bounded preview/artifact contracts.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p605-exact-backend-preview-evidence.txt`
- `.complex-problems/L20260516-222011/tmp/p605-raw-bytes-risk-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p605-focused-tests.txt`
