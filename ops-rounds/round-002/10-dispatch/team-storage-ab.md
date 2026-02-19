# Round 002 Dispatch - Storage-A/B Team

## Objective
Convert storage work from documentation baseline to executable, verifiable services.

## Hard Tasks
1. Deliver runnable `backup` and `restore` scripts for both services.
2. Run one full restore validation exercise and publish result.
3. Add independent CI checks with health and read/write smoke tests.
4. Align file/result API fields with contract baseline and record mismatches.

## Acceptance Criteria
- Backup and restore scripts run successfully in validation environment.
- Both services pass health and read/write smoke tests.
- Contract field alignment report is complete.

## Required Evidence
- script paths and validation output summary
- CI run summary for both services
- contract alignment report path

## Status
- owner: Storage-A/B Team
- due: 2026-02-26
- status: IN_PROGRESS

## Execution Breakdown (Round 002)

### Task 1: Backup/Restore scripts for both services
- owner: Storage-A/B Team
- due: 2026-02-22
- status: DONE
- evidence:
  - commands:
    - `bash novaic-backend/scripts/storage_ab_validate_restore.sh`
  - artifacts:
    - `novaic-backend/scripts/storage_ab_backup.sh`
    - `novaic-backend/scripts/storage_ab_restore.sh`
    - `novaic-backend/scripts/storage_ab_validate_restore.sh`
  - docs:
    - `week1-team-workorders/storage-ab/backup-restore-runbook-v0.1.md`
    - `ops-rounds/round-002/20-reports/team-storage-ab-validation-latest.md`
- dependencies:
  - service repos split completion for `novaic-file-service` and `novaic-tool-result-service`
  - CI runner availability
- risk_level: P0

### Task 2: Full restore validation run and publish result
- owner: Storage-A/B Team
- due: 2026-02-23
- status: DONE
- evidence:
  - commands:
    - `bash novaic-backend/scripts/storage_ab_validate_restore.sh`
  - result_summary:
    - restore drill finished with `VALIDATION_OK=true`
    - backup output includes `BACKUP_DIR` and `manifest.json` path
    - restore output includes `RESTORE_OK=true`
  - docs:
    - `ops-rounds/round-002/20-reports/team-storage-ab-validation-latest.md`
- dependencies:
  - runnable restore scripts
  - non-production validation environment
- risk_level: P0

### Task 3: Independent CI checks with health and read/write smoke
- owner: Storage-A/B Team
- due: 2026-02-24
- status: IN_PROGRESS
- evidence:
  - commands:
    - `bash novaic-backend/scripts/storage_ab_smoke.sh`
  - artifacts:
    - `novaic-backend/scripts/storage_ab_smoke.sh`
  - docs:
    - `ops-rounds/round-002/20-reports/team-storage-ab-smoke-latest.md`
    - `week1-team-workorders/storage-ab/sla-v0.1.md`
    - `week1-team-workorders/storage-ab/data-model-v0.1.md`
- dependencies:
  - independent repo pipelines
  - smoke test cases in service repos
- risk_level: P1

### Task 4: Contract field alignment report
- owner: Storage-A/B Team
- due: 2026-02-25
- status: IN_PROGRESS
- evidence:
  - docs: `week1-team-workorders/storage-ab/data-model-v0.1.md`
  - docs: `week1-team-workorders/storage-ab/sla-v0.1.md`
  - docs: `ops-rounds/round-002/20-reports/team-storage-ab-contract-alignment.md`
- dependencies:
  - latest contract baseline from Platform/API
- risk_level: P1

## Daily Kickoff Update (2026-02-19)
- owner: Storage-A/B Team
- due: 2026-02-19 18:00
- status: IN_PROGRESS
- evidence:
  - docs: `ops-rounds/round-002/20-reports/team-storage-ab-report.md`
  - docs: `ops-rounds/round-002/20-reports/team-storage-ab-contract-alignment.md`
- dependencies:
  - non-production validation environment for restore drill
  - contract baseline confirmation from Platform/API
- risk_level: P0
