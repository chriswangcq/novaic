# Week 1 Task Order - Storage-A/B Team

## Team
Storage-A/B Team

## Mission
Split file and tool-result storage into independent services with baseline reliability guarantees.

## Current Execution Status (Start)
- Owner: Storage-A/B Team
- Start date: 2026-02-19
- Sprint target: Week 1 D1-D5
- Status: In Progress

### Workstream Progress
- [x] Scope baseline confirmed for both services
- [x] Initial SLA draft created
- [x] Backup/restore runbook draft created
- [x] Data model baseline draft created
- [ ] Repo split and code migration complete
- [ ] Backup/restore scripts implemented and validated in CI
- [ ] `v0.1.0-rc1` released for both services

## Scope
- Create `novaic-file-service` repo
- Create `novaic-tool-result-service` repo
- Migrate service code and startup modules
- Define data models, retention, backup and restore scripts
- Enable independent CI/release for both repos

## Execution Plan (D1-D5)
- D1: Initialize both repos and migrate code
- D2: Finalize schema/index strategy and service config variables
- D3: Implement backup and restore scripts with validation step
- D4: Integrate CI for both repos and add health/read-write tests
- D5: Publish `v0.1.0-rc1` for both services and SLA draft

## Acceptance Criteria
- Both services build/test/run independently
- Data paths and config are monorepo-independent
- Backup and restore scripts complete successfully in test run
- API contracts are aligned with shared contracts

## Deliverables
- `novaic-file-service` repo
- `novaic-tool-result-service` repo
- schema and retention docs
- backup/restore scripts
- two `v0.1.0-rc1` releases
- baseline execution artifacts:
  - `week1-team-workorders/storage-ab/sla-v0.1.md`
  - `week1-team-workorders/storage-ab/backup-restore-runbook-v0.1.md`
  - `week1-team-workorders/storage-ab/data-model-v0.1.md`

## Dependencies and Coordination
- Coordinate with Tools Team and API Team for API usage alignment
- Coordinate with Platform Team for contract publishing

## Risk Escalation
- Data corruption, failed restore validation, or contract mismatch is release blocker
