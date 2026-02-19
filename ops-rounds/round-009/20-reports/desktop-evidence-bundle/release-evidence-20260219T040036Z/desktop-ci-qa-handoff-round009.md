# Desktop CI/QA Handoff - Round 009

## Canonical Governance Reference
- `ops-rounds/governance/desktop-operability-policy.md`
- `ops-rounds/governance/desktop-operator-quick-checklist.md`

## Finalized Policy
- policy_id: `desktop-operability-policy-v1`
- owner:
  - Desktop Team
  - Platform CI Owner
  - QA Release Owner
- cadence:
  - CI replay gate: every PR/push run
  - GUI installer replay: release checkpoint + weekly QA audit

## Required Handoff Evidence
- replay command output:
  - `novaic-app/scripts/validate_fresh_profile.sh`
- replay files:
  - `fresh-profile-*-summary.txt`
  - `fresh-profile-*-startup.log`
  - `fresh-profile-*-startup-diagnostics.jsonl`
  - `fresh-profile-*-metadata.txt`
- bundle outputs:
  - `release-evidence-*.tar.gz`
  - `release-evidence-*-manifest.txt`

## CI Enforcement Link
- `.github/workflows/ci.yml` job `desktop-operability` enforces script replay and policy marker checks.
