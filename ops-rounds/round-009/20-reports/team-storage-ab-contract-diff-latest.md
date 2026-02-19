# Storage-A/B Contract Diff Evidence — Round 009

- status: DONE
- round: 009
- executed_at_utc: 2026-02-19T03:58:58Z
- command: `bash novaic-backend/scripts/storage_ab_contract_diff.sh --schema-path contracts/schema/storage-api.v1.schema.json`
- schema_path: `contracts/schema/storage-api.v1.schema.json`
- schema_version: `v1.0.0`
- schema_version_check: PASS
- schema_owner_check: PASS
- CONTRACT_DIFF_OK: true
- evergreen_evidence: `contracts/evidence/storage-contract-diff-latest.md`

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
