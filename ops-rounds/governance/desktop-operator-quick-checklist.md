# Desktop Operator Quick Checklist

## Purpose
Quick non-author verification before declaring desktop release evidence complete.

## Preconditions
- Desktop build artifacts exist:
  - `novaic-app/src-tauri/target/release/bundle/macos/NovAIC.app`
  - `novaic-app/src-tauri/target/release/bundle/dmg/NovAIC_0.3.0_aarch64.dmg`

## Steps
1. Run Rust build check:
   - `cargo check --manifest-path "novaic-app/src-tauri/Cargo.toml"`
2. Replay fresh-profile validation:
   - `RUN_LABEL="<label>" OPERATOR_ID="<operator>" EVIDENCE_DIR="<round evidence dir>" novaic-app/scripts/validate_fresh_profile.sh`
3. Confirm replay summary pass criteria:
   - `event_count>=10`
   - `error_timeout_count=0`
4. Generate evidence bundle:
   - `novaic-app/scripts/build_desktop_evidence_bundle.sh "<round dir>"`
5. Confirm bundle manifest exists and has checksum:
   - `<round>/20-reports/desktop-evidence-bundle/*-manifest.txt`

## Pass/Fail
- PASS only if all commands succeed and evidence files exist.
- FAIL if any command fails or `error_timeout_count>0`.
