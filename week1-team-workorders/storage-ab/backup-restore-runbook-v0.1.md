# Storage-A/B Backup and Restore Runbook v0.1

## Services Covered
- Storage-A: `novaic-file-service`
- Storage-B: `novaic-tool-result-service`

## Backup Strategy

### A) Storage-A (`novaic-file-service`)
- Data classes:
  - File binary objects (object store)
  - File metadata (relational database)
- Backup policy:
  - Object store:
    - Cross-zone replication enabled
    - Daily immutable snapshot at 02:00 UTC
    - 35-day snapshot retention
  - Metadata DB:
    - Full backup once per day at 01:00 UTC
    - Incremental/WAL shipping every 5 minutes
    - 35-day retention

### B) Storage-B (`novaic-tool-result-service`)
- Data classes:
  - Tool execution result records
  - Optional artifact references
- Backup policy:
  - Results DB:
    - Full backup once per day at 01:30 UTC
    - Incremental/WAL shipping every 5 minutes
    - 35-day retention
  - Artifact blobs (if enabled):
    - Daily immutable snapshot at 02:30 UTC
    - 35-day retention

## Encryption and Access Control
- Backup at rest: AES-256 (KMS managed key)
- Backup in transit: TLS 1.2+
- Restore permissions: on-call SRE + service owner approval
- Every restore action must produce audit logs and ticket reference.

## Restore Procedures

### 1) Metadata/Results DB Point-in-Time Restore (PITR)
1. Freeze write traffic to impacted service.
2. Identify target timestamp (`T_restore`) from incident timeline.
3. Provision recovery instance from last full backup.
4. Replay WAL/incremental logs up to `T_restore`.
5. Run integrity checks:
   - row counts by key tables
   - checksum/hash verification sample set
   - latest successful write id continuity
6. Switch service read/write endpoint to recovered DB.
7. Run smoke tests:
   - create/read/update/delete minimal cases
   - downstream API caller validation (gateway/tools/runtime)
8. Close freeze and monitor error rate for 30 minutes.

### 2) Object/Artifact Restore
1. Identify impacted bucket/prefix and time window.
2. Restore from immutable snapshot into staging bucket.
3. Run consistency diff (object count + checksum sampling).
4. Promote restored objects to production bucket/prefix.
5. Reconcile metadata references if object keys changed.
6. Run file fetch/read verification checks.

## Validation and Drill Policy
- Weekly automated backup verification:
  - backup completeness
  - checksum validation
  - restorable manifest generation
- Bi-weekly restore drill:
  - one Storage-A scenario + one Storage-B scenario
  - must meet RTO/RPO targets from SLA
- Drill output must include:
  - elapsed restore time
  - recovered data delta
  - failed checks and remediation items

## Executable Scripts (Round 002)
- Backup: `novaic-backend/scripts/storage_ab_backup.sh`
- Restore: `novaic-backend/scripts/storage_ab_restore.sh`
- Validation drill: `novaic-backend/scripts/storage_ab_validate_restore.sh`

Example:
- `bash novaic-backend/scripts/storage_ab_validate_restore.sh`

## Failure Handling
- Backup job failure:
  - auto-retry up to 3 times (exponential backoff)
  - if still failing: raise SEV-2 after 30 minutes
- Replication lag > 15 minutes:
  - page on-call
  - block risky schema changes until lag normalizes
- Integrity check failure:
  - mark backup set as invalid
  - select previous valid restore point
  - create incident ticket

## Operational Checklist (D3 Exit Gate)
- [ ] Backup jobs configured in both services
- [ ] Immutable storage lock enabled
- [ ] Restore scripts tested on non-prod environment
- [ ] PITR validated for Storage-A and Storage-B
- [ ] Drill report archived and shared with API/Tools teams
