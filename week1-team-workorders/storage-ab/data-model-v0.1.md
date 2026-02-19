# Storage-A/B Data Model Baseline v0.1

## Goal
Define independent, migration-safe data models for:
- Storage-A: `novaic-file-service`
- Storage-B: `novaic-tool-result-service`

The model is designed for:
- service autonomy
- clear retention ownership
- restore friendliness and auditability

## Storage-A (`novaic-file-service`)

### Core Entities

#### 1) `files`
- `id` (uuid, pk)
- `tenant_id` (varchar, indexed)
- `workspace_id` (varchar, indexed)
- `object_key` (varchar, unique)
- `filename` (varchar)
- `mime_type` (varchar)
- `size_bytes` (bigint)
- `checksum_sha256` (char(64))
- `storage_class` (varchar)  # standard/cold/archive
- `encryption_key_id` (varchar, nullable)
- `created_at` (timestamp, indexed)
- `updated_at` (timestamp)
- `deleted_at` (timestamp, nullable, indexed)  # soft delete

Indexes:
- `idx_files_tenant_workspace_created` on (`tenant_id`, `workspace_id`, `created_at`)
- `idx_files_checksum` on (`checksum_sha256`)
- unique `uq_files_object_key` on (`object_key`)

#### 2) `file_access_logs` (optional in Week 1, recommended)
- `id` (bigserial, pk)
- `file_id` (uuid, indexed, fk -> files.id)
- `actor_id` (varchar)
- `action` (varchar)  # upload/download/delete/restore
- `request_id` (varchar, indexed)
- `created_at` (timestamp, indexed)

Retention:
- `files`: business-defined, default soft-delete retention 30 days
- `file_access_logs`: 90 days hot, then archive

## Storage-B (`novaic-tool-result-service`)

### Core Entities

#### 1) `tool_results`
- `id` (uuid, pk)
- `tenant_id` (varchar, indexed)
- `task_id` (varchar, indexed)
- `run_id` (varchar, indexed)
- `agent_id` (varchar, indexed)
- `tool_name` (varchar, indexed)
- `status` (varchar, indexed)  # success/failed/timeout/cancelled
- `input_digest` (char(64), nullable)
- `output_json` (jsonb)
- `error_code` (varchar, nullable)
- `error_message` (text, nullable)
- `duration_ms` (integer)
- `artifact_ref` (varchar, nullable)
- `created_at` (timestamp, indexed)
- `expires_at` (timestamp, indexed)  # TTL boundary

Indexes:
- `idx_tool_results_task_run` on (`task_id`, `run_id`)
- `idx_tool_results_agent_created` on (`agent_id`, `created_at`)
- `idx_tool_results_status_created` on (`status`, `created_at`)
- `idx_tool_results_expires_at` on (`expires_at`)

#### 2) `tool_result_events` (append-only)
- `id` (bigserial, pk)
- `result_id` (uuid, indexed, fk -> tool_results.id)
- `event_type` (varchar)  # created/retried/completed/expired
- `payload_json` (jsonb)
- `created_at` (timestamp, indexed)

Retention:
- `tool_results`: default 30 days (configurable per tenant)
- `tool_result_events`: 30 days hot + optional archive 180 days

## Cross-Service Conventions
- IDs use UUID v4 generated service-side.
- `created_at` always UTC.
- Soft delete preferred for user-facing records.
- Schema changes follow additive-first migration:
  1. add nullable field
  2. dual-write/read compatibility window
  3. backfill
  4. make non-null/remove old field in next release

## Data Integrity and Consistency Rules
- `object_key` must be globally unique in Storage-A.
- `task_id + run_id + tool_name` should be idempotent in Storage-B write path.
- Deleting file metadata without object deletion is forbidden except in recovery mode.
- Expired tool results are removed by background sweeper with batch limit and retry-safe cursor.

## Config Variables (Week 1 minimum)
- `FILE_RETENTION_DAYS`
- `FILE_SOFT_DELETE_DAYS`
- `TOOL_RESULT_RETENTION_DAYS`
- `RESULT_SWEEPER_BATCH_SIZE`
- `BACKUP_BUCKET`
- `BACKUP_KMS_KEY_ID`

## Migration Checklist
- [ ] Initial schema migration scripts created in each repo
- [ ] Index creation verified on representative dataset
- [ ] Retention sweeper tested with dry-run mode
- [ ] Backfill strategy documented for future incompatible changes
