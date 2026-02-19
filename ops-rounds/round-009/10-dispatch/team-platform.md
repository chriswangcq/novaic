# Round 009 Dispatch - Platform Team

## Objective
Eliminate governance/state drift and publish final operational index.

## Mandatory Tasks
1. Reconcile status drift in prior round reports (state must match evidence).
2. Publish governance index v1.0 as canonical entrypoint.
3. Add CI check to fail on unresolved `DONE_WITH_GAPS` without owner+deadline.

## Acceptance Commands
- `rg "DONE_WITH_GAPS|IN_PROGRESS|status:" ops-rounds/round-00*/20-reports -g "team-*-report.md"`
- `rg "governance-index|owner|deadline|DONE_WITH_GAPS" ops-rounds/governance .github -g "*.md" -g "*.yml"`

## Due / Status
- due: 2026-02-24 18:00
- status: DONE

## Task Tracking
- task: mandatory-1-reconcile-status-drift
  owner: Platform Team
  due: 2026-02-24 18:00
  status: DONE
  evidence:
    - `ops-rounds/round-007/20-reports/team-platform-report.md`
    - `ops-rounds/round-006/20-reports/team-platform-report.md`
    - `ops-rounds/round-005/20-reports/team-platform-report.md`
    - `ops-rounds/round-004/20-reports/team-platform-report.md`
    - `ops-rounds/round-003/20-reports/team-platform-report.md`
    - `ops-rounds/round-002/20-reports/team-platform-report.md`
  dependencies:
    - none
  risk_level: low

- task: mandatory-2-governance-index-v1
  owner: Platform Team
  due: 2026-02-24 18:00
  status: DONE
  evidence:
    - `ops-rounds/governance/governance-index.md` (version: v1.0)
  dependencies:
    - none
  risk_level: low

- task: mandatory-3-ci-check-done-with-gaps-metadata
  owner: Platform Team
  due: 2026-02-24 18:00
  status: DONE
  evidence:
    - `.github/workflows/ci.yml` (job `governance-report-integrity`)
  dependencies:
    - none
  risk_level: low
