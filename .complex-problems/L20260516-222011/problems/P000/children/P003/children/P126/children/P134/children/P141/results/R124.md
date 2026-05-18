# Workspace payload store and blob externalization audit result

## Summary

Completed the workspace payload store audit. No code change was required in this slice. Payload storage is explicit and reference-oriented: full payloads are stored under `payloads/*.json` or external blob refs, while normal step/context projections carry compact observations and payload pointers.

## Done

- Mapped payload read error/manifest status update:
  - `novaic-cortex/novaic_cortex/workspace.py:140-181`
  - Read failures update operational payload manifest status/error when a manifest exists.
- Mapped payload write:
  - `workspace.py:563-621`
  - Requires non-empty string `payload_ref`.
  - Encodes payload and computes SHA-256.
  - Uses `BlobPayloadPolicy` to choose local JSON versus external blob.
  - External blob requires payload blob client and records `content_type="external_blob"`.
  - Local payload records `content_type="local_json"` and stores content in the scope-local payload file.
  - Operational manifest records `payload_ref`, `source_payload_ref`, `root_scope_id`, `scope_id`, `step_ref`, `blob_ref`, MIME, size, hash, status, and retention class.
- Mapped payload read:
  - `workspace.py:623-671`
  - Reads by hashed payload ref path.
  - Fails loudly on missing/corrupt/ref mismatch/blob unavailable.
  - External blob records are fetched only through the payload blob client.
- Mapped write-step payload interaction:
  - `workspace.py:719-735`
  - Inline raw `payload` is removed from the durable step file and written through `write_payload`.
  - Stable `step_ref` is preserved separately from actual/externalized `payload_ref`.
  - Observation receives the actual payload ref for pointer-based inspection.
- Verified explicit payload inspection API behavior:
  - `novaic-cortex/tests/test_payload_inspection_api.py`
  - Read/search are bounded.
  - Summarize/QA redact and bound model input/output.

## Verification

- Ran:

```bash
PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_step_index_outcome.py novaic-cortex/tests/test_payload_inspection_api.py
```

- Result:

```text
25 passed in 0.42s
```

- Covered behaviors include:
  - local payload externalization without mutating input
  - step write removing inline raw payload from durable step file
  - large payload externalization to blob ref
  - readback from blob ref
  - manifest source ref, blob ref, stable step ref, status, retention class
  - missing/corrupt/ref-mismatch/blob-fetch/missing-client errors updating manifest
  - large payload requiring blob client when policy externalizes
  - bounded payload read/search/summarize/QA APIs

## Known Gaps

- Step index metadata details are handled by sibling P142.
- `context.jsonl` projection classification is handled by sibling P143.
- API dual-write/materialization call sites are handled by sibling P144.

## Artifacts

- Source: `novaic-cortex/novaic_cortex/workspace.py`
- Tests: `novaic-cortex/tests/test_step_index_outcome.py`
- Tests: `novaic-cortex/tests/test_payload_inspection_api.py`
