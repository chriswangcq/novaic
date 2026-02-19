# Round 008 Dispatch - Platform Team

## Objective
Finalize governance references and eliminate status/evidence mismatch.

## Mandatory Tasks
1. Align team statuses with actual evidence state across round reports.
2. Publish one stable governance index pointing to all active policies/checklists/scripts.
3. Ensure compatibility counting rule is referenced from CI and governance index.

## Acceptance Commands
- `rg "status:|DONE_WITH_GAPS|IN_PROGRESS" ops-rounds/round-007/20-reports -g "team-*-report.md"`
- `rg "compatibility|governance|ownership|evidence" ops-rounds/governance contracts .github -g "*.md" -g "*.yml"`

## Due / Status
- due: 2026-02-23 18:00
- status: DONE

## Task Tracking
- task: mandatory-1-status-alignment
  owner: Platform Team
  due: 2026-02-23 18:00
  status: DONE
  evidence:
    - `ops-rounds/round-007/20-reports/team-platform-report.md` (synced to DONE)
    - `contracts/STORAGE_SCHEMA_OWNERSHIP_CHECKLIST.md` (tri-party signed)
  dependencies:
    - none
  risk_level: low

- task: mandatory-2-governance-index
  owner: Platform Team
  due: 2026-02-23 18:00
  status: DONE
  evidence:
    - `ops-rounds/governance/governance-index.md`
  dependencies:
    - none
  risk_level: low

- task: mandatory-3-counting-rule-refs
  owner: Platform Team
  due: 2026-02-23 18:00
  status: DONE
  evidence:
    - `.github/workflows/ci.yml` (`compatibility-matrix` checks effective rule + governance index)
    - `ops-rounds/governance/effective-compatibility-counting-rule.md`
    - `ops-rounds/governance/governance-index.md`
  dependencies:
    - none
  risk_level: low
