# Round 006 Dispatch - Platform Team

## Objective
Finalize governance counting rules and remove evidence ambiguity.

## Mandatory Tasks
1. Finalize and publish official counting rule for `>=5` compatibility consumption evidence.
2. Update CI/doc checks to reflect finalized counting rule.
3. Co-sign storage schema ownership checklist with API + Storage-A/B.

## Acceptance Commands
- `rg "compatibility|counting rule|ownership" contracts .github ops-rounds -g "*.md" -g "*.yml"`
- `pytest -q tests/unit/common/test_strict_config.py`

## Due / Status
- due: 2026-02-24 18:00
- status: IN_PROGRESS

## Task Tracking
- task: mandatory-1-finalize-counting-rule
  owner: Platform Team
  due: 2026-02-24 18:00
  status: DONE
  evidence:
    - `ops-rounds/governance/compatibility-consumption-counting-rule.md`
    - `ops-rounds/governance/compatibility-consumption-evidence-latest.md`
  dependencies:
    - reviewer confirmation of counting-rule interpretation
  risk_level: medium

- task: mandatory-2-update-ci-doc-checks
  owner: Platform Team
  due: 2026-02-24 18:00
  status: DONE
  evidence:
    - `.github/workflows/ci.yml` (`compatibility-matrix` validation upgraded)
  dependencies:
    - none
  risk_level: low

- task: mandatory-3-storage-ownership-cosign
  owner: Platform Team
  due: 2026-02-24 18:00
  status: IN_PROGRESS
  evidence:
    - `contracts/STORAGE_SCHEMA_OWNERSHIP_CHECKLIST.md` (Platform signed)
  dependencies:
    - Storage-A/B Team co-sign required for full closure
  risk_level: medium
