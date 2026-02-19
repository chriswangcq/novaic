# Desktop Operability Policy (Stable)

## Policy ID
- `desktop-operability-policy-v1`

## Scope
Desktop release-gate operability checks for `novaic-app`.

## Final Policy
- CI policy:
  - Enforce scriptable replay checks on every CI run for desktop gate.
  - Required commands:
    - `cargo check --manifest-path "novaic-app/src-tauri/Cargo.toml"`
    - `novaic-app/scripts/validate_fresh_profile.sh`
- GUI installer policy:
  - GUI installer replay is executed on QA cadence, not every CI run.

## Owner
- Primary owner: Desktop Team
- Governance co-owner: Platform CI Owner
- QA owner: QA Release Owner

## Cadence
- CI scriptable replay: every PR/push CI run.
- GUI installer replay:
  - mandatory at release checkpoint
  - weekly audit cadence during active release cycle

## Evidence Requirements
- Script replay evidence (CI or local replay):
  - `fresh-profile-*-summary.txt`
  - `fresh-profile-*-startup.log`
  - `fresh-profile-*-startup-diagnostics.jsonl`
  - `fresh-profile-*-metadata.txt`
- Release evidence bundle:
  - generated via `novaic-app/scripts/build_desktop_evidence_bundle.sh`
  - must include archive + manifest with checksum

## Failure Rule
- If replay summary reports `error_timeout_count>0`, release gate is blocked until rerun passes.
