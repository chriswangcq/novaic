# Round 002 - Storage-A/B Contract Alignment (Working)

## Owner and Status
- owner: Storage-A/B Team
- due: 2026-02-25
- status: IN_PROGRESS

## Scope
Align file/result API fields with contract baseline and record mismatches.

## Baseline Inputs
- `week1-team-workorders/storage-ab/data-model-v0.1.md`
- `week1-team-workorders/storage-ab/sla-v0.1.md`
- `contracts/` (Platform contract baseline, pending final cross-check)

## Preliminary Field Matrix

### Storage-A (`novaic-file-service`)
- required identity fields:
  - `id`
  - `tenant_id`
  - `workspace_id`
- file payload fields:
  - `object_key`
  - `filename`
  - `mime_type`
  - `size_bytes`
  - `checksum_sha256`
- lifecycle fields:
  - `created_at`
  - `updated_at`
  - `deleted_at`

### Storage-B (`novaic-tool-result-service`)
- execution identity fields:
  - `id`
  - `task_id`
  - `run_id`
  - `agent_id`
  - `tool_name`
- result payload fields:
  - `status`
  - `output_json`
  - `error_code`
  - `error_message`
  - `duration_ms`
  - `artifact_ref`
- retention fields:
  - `created_at`
  - `expires_at`

## Current Mismatch Findings
- No code-level mismatch is claimed yet.
- Contract-to-implementation diff still pending executable verification against latest `contracts/`.

## Required Verification Evidence (Pending)
- commands:
  - contract schema inspection command list
  - implementation field extraction command list
- result summary:
  - exact matched fields
  - missing fields
  - extra fields
- output artifact:
  - final mismatch matrix in this file (or follow-up file)

## Next Actions
- Pull latest Platform/API contract baseline and run field-level diff.
- Update this file from `IN_PROGRESS` to `DONE` only when command outputs and diff summary are attached.
