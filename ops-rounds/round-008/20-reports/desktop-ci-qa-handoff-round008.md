# Desktop CI/QA Handoff - Round 008

## Final Policy (Locked)
- policy_source: `ops-rounds/governance/desktop-operability-policy.md`
- policy_id: `desktop-operability-policy-v1`
- policy_owner:
  - Desktop Team
  - Platform CI Owner
  - QA Release Owner
- cadence:
  - CI replay gate: every run
  - GUI installer replay: release checkpoint + weekly QA audit

## CI Enforcement Scope
- workflow: `.github/workflows/ci.yml`
- gate job: `desktop-operability`
- enforced commands:
  - `cargo check --manifest-path "novaic-app/src-tauri/Cargo.toml"`
  - `npm run tauri:build`
  - `novaic-app/scripts/validate_fresh_profile.sh`

## QA Execution Scope
- execute GUI installer replay on cadence
- verify evidence package includes:
  - replay summary/log/diagnostics/metadata
  - evidence bundle archive + manifest checksum

## Final Handoff Links
- `ops-rounds/governance/desktop-operability-policy.md`
- `ops-rounds/governance/desktop-operator-quick-checklist.md`
- `ops-rounds/round-008/20-reports/desktop-clean-profile-replay-round008.md`
