# Round 007 Dispatch - Platform Team

## Objective
Close governance ambiguity and unblock final PASS.

## Mandatory Tasks
1. Drive tri-party storage checklist to fully signed state.
2. Provide remote CI evidence export for storage-governance run (if Storage toolchain lacks `gh`).
3. Finalize and publish compatibility counting rule as "effective rule" reference.

## Acceptance Commands
- `rg "SIGNED|PENDING" contracts/STORAGE_SCHEMA_OWNERSHIP_CHECKLIST.md`
- `rg "compatibility-consumption-counting-rule|effective" ops-rounds/governance -g "*.md"`

## Due / Status
- due: 2026-02-23 18:00
- status: IN_PROGRESS

## Task Tracking
- task: mandatory-1-tri-party-storage-checklist
  owner: Platform Team
  due: 2026-02-23 18:00
  status: IN_PROGRESS
  evidence:
    - `contracts/STORAGE_SCHEMA_OWNERSHIP_CHECKLIST.md`
  dependencies:
    - Storage-A/B Team co-sign
  risk_level: medium

- task: mandatory-2-remote-ci-evidence-export
  owner: Platform Team
  due: 2026-02-23 18:00
  status: DONE
  evidence:
    - `novaic-backend/scripts/export_storage_governance_ci_evidence.py`
    - `ops-rounds/governance/storage-governance-ci-trace-latest.md`
    - `contracts/STORAGE_SCHEMA_GOVERNANCE.md` (usage documented)
  dependencies:
    - optional `GITHUB_TOKEN` when `gh` is unavailable
  risk_level: low

- task: mandatory-3-effective-counting-rule-reference
  owner: Platform Team
  due: 2026-02-23 18:00
  status: DONE
  evidence:
    - `ops-rounds/governance/effective-compatibility-counting-rule.md`
    - `ops-rounds/governance/compatibility-consumption-counting-rule.md`
    - `.github/workflows/ci.yml`
  dependencies:
    - none
  risk_level: low
