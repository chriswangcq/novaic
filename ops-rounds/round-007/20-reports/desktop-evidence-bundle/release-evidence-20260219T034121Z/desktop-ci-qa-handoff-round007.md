# Desktop CI/QA Handoff - Round 007 (Final Policy)

## Finalized Policy
- policy_decision_id: `desktop-operability-policy-v1`
- policy: **Hybrid**
  - CI enforces scriptable fresh-profile replay on every run.
  - GUI installer replay is executed on QA cadence (release checkpoint / weekly audit), not every CI run.
- policy_owner: Desktop Team + QA Owner
- effective_from: 2026-02-19

## CI Gate Scope (Implemented)
- workflow: `.github/workflows/ci.yml`
- job: `desktop-operability`
- enforced steps:
  - `cargo check --manifest-path "novaic-app/src-tauri/Cargo.toml"`
  - `npm run tauri:build`
  - `novaic-app/scripts/validate_fresh_profile.sh` (CI operator replay)
  - upload replay evidence artifact

## QA Cadence Scope
- QA executes GUI installer replay by cadence:
  - release checkpoint (mandatory)
  - weekly audit (recommended)
- replay references:
  - `novaic-app/scripts/validate_fresh_profile.sh`
  - `ops-rounds/round-007/20-reports/desktop-clean-profile-replay-round007.md`

## Failure-Mode Examples

### Example A - Missing app bundle
- trigger:
  - `novaic-app/scripts/validate_fresh_profile.sh "/tmp/not-exists/NovAIC.app"`
- expected:
  - non-zero exit
  - `ERROR: app bundle not found`

### Example B - Startup blocking error chain
- trigger:
  - dependency startup failure resulting in `error`/`timeout` diagnostics
- expected:
  - `fresh-profile-*-summary.txt` contains `error_timeout_count>0`
  - script exits non-zero
- action:
  - inspect diagnostics jsonl and classify using:
    - `ops-rounds/round-002/20-reports/desktop-startup-triage-matrix.md`

## Required Evidence Package
- `ops-rounds/round-007/20-reports/desktop-evidence/fresh-profile-*-summary.txt`
- `ops-rounds/round-007/20-reports/desktop-evidence/fresh-profile-*-startup.log`
- `ops-rounds/round-007/20-reports/desktop-evidence/fresh-profile-*-startup-diagnostics.jsonl`
- `ops-rounds/round-007/20-reports/desktop-evidence/fresh-profile-*-metadata.txt`
- `ops-rounds/round-007/20-reports/desktop-evidence-bundle/*.tar.gz`
- `ops-rounds/round-007/20-reports/desktop-evidence-bundle/*-manifest.txt`
