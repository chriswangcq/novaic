# Round 002 Report - Storage-A/B Team

## Task 1
- task: Create `split-exec/storage-a-repo-candidate.md` and `split-exec/storage-b-repo-candidate.md` with extraction boundaries and owners.
- evidence:
  - command:
    - `test -f "novaic-control-plane/rounds/round-002/split-exec/storage-a-repo-candidate.md" && echo "STORAGE_A_CANDIDATE_EXISTS=PASS"`
    - `test -f "novaic-control-plane/rounds/round-002/split-exec/storage-b-repo-candidate.md" && echo "STORAGE_B_CANDIDATE_EXISTS=PASS"`
  - expected_marker:
    - `STORAGE_A_CANDIDATE_EXISTS=PASS`
    - `STORAGE_B_CANDIDATE_EXISTS=PASS`
  - summary:
    - PASS; Storage-A and Storage-B repo candidate artifacts were created with owner, extraction paths, and runtime entrypoints.
  - artifact_path:
    - `novaic-control-plane/rounds/round-002/split-exec/storage-a-repo-candidate.md`
    - `novaic-control-plane/rounds/round-002/split-exec/storage-b-repo-candidate.md`
- status: DONE

## Task 2
- task: Create `split-exec/storage-consumer-impact-replay.md` covering schema and restore/smoke consumer impact checks.
- evidence:
  - command:
    - `test -f "novaic-control-plane/rounds/round-002/split-exec/storage-consumer-impact-replay.md" && echo "STORAGE_CONSUMER_IMPACT_EXISTS=PASS"`
  - expected_marker:
    - `STORAGE_CONSUMER_IMPACT_EXISTS=PASS`
  - summary:
    - PASS; consumer impact replay artifact documents schema/openapi scope and restore/smoke replay gates for split execution.
  - artifact_path:
    - `novaic-control-plane/rounds/round-002/split-exec/storage-consumer-impact-replay.md`
- status: DONE

## Task 3
- task: Run storage validate/restore/smoke replay and publish baseline for both domains.
- evidence:
  - command:
    - `bash "novaic-backend/scripts/storage_ab_validate_restore.sh" --report-path "novaic-control-plane/rounds/round-002/20-reports/team-storage-ab-validation-baseline.md"`
  - expected_marker:
    - `VALIDATION_OK=true`
  - summary:
    - PASS; validate/restore baseline succeeded and report contains restore file/db checks as PASS.
  - artifact_path:
    - `novaic-control-plane/rounds/round-002/20-reports/team-storage-ab-validation-baseline.md`
- evidence:
  - command:
    - `bash "novaic-backend/scripts/storage_ab_smoke.sh" --report-path "novaic-control-plane/rounds/round-002/20-reports/team-storage-ab-smoke-baseline.md"`
  - expected_marker:
    - `SMOKE_OK=true`
  - summary:
    - PASS; smoke baseline succeeded with file service and tool result service health/write-read checks all PASS.
  - artifact_path:
    - `novaic-control-plane/rounds/round-002/20-reports/team-storage-ab-smoke-baseline.md`
- evidence:
  - command:
    - `bash "novaic-backend/scripts/storage_ab_backup.sh" --data-dir "<tmp>" --backup-root "<tmp>" --label "round002-baseline"`
    - `bash "novaic-backend/scripts/storage_ab_restore.sh" --backup-dir "<resolved>" --target-dir "<tmp>" --yes`
  - expected_marker:
    - `RESTORE_OK=true`
  - summary:
    - PASS; standalone backup/restore replay succeeded and post-check confirmed restored file and DB row.
  - artifact_path:
    - `novaic-control-plane/rounds/round-002/20-reports/team-storage-ab-restore-baseline.md`
- status: DONE

## Decision Needed (optional)
- issue:
- options:
- recommendation:
- impact:
- owner:
- target_round:

## Team status
- status: DONE
- blocker: none
