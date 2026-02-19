# Storage-A/B Contract Diff Evidence

- status: DONE
- executed_at_utc: 2026-02-19T03:05:58Z
- command: `bash novaic-backend/scripts/storage_ab_contract_diff.sh`
- schema_path: `contracts/schema/storage-api.v1.schema.json`
- schema_version: `v1.0.0`
- schema_owners: `['Platform Team', 'API Team', 'Storage-A/B Team']`
- schema_version_check: PASS
- schema_owner_check: PASS
- baseline_docs:
  - `week1-team-workorders/storage-ab/data-model-v0.1.md`
  - `contracts/schema/storage-api.v1.schema.json`
  - `ops-rounds/round-005/10-dispatch/team-storage-ab.md`

## Matrix
### file_service.from-base64 response
- matched: ['category', 'filename', 'mime_type', 'size', 'url']
- missing: []
- extra: []

### tool_result_service.create response
- matched: ['result_id', 'success']
- missing: []
- extra: []

### tool_result_service.get response
- matched: ['normalized', 'result_id', 'success']
- missing: []
- extra: []

### tool_result_service.normalized payload
- matched: ['display_files', 'files_created', 'text']
- missing: []
- extra: []

## Raw Samples
- file_service.from-base64:
  - `{"url": "/api/files/documents/agent-contract/1771470358344_271cfe5c.pdf", "category": "documents", "size": 21, "mime_type": "application/pdf", "filename": "1771470358344_271cfe5c.pdf"}`
- tool_result_service.create:
  - `{"success": true, "result_id": "trs_df6eb374"}`
- tool_result_service.get:
  - `{"success": true, "result_id": "trs_df6eb374", "normalized": {"text": "ok", "files_created": [{"url": "/api/files/documents/agent-contract/1771470358344_271cfe5c.pdf", "filename": "contract.pdf", "modality": "resource"}], "display_files": []}}`

## Notes
- contract diff is schema-backed and executable against live service responses.
